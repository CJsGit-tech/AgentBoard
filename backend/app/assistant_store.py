"""Durable Assistant state. Secrets never enter this module."""
import hashlib
import json
from uuid import uuid4

from psycopg.types.json import Jsonb

from .db import connect
from .store import Problem, get_row, mutate, public
from . import reviews

TERMINAL = {'Completed', 'Failed', 'Cancelled'}
ACTIVE = {'Queued', 'Running'}


def safe(row):
    if row is None:
        raise Problem(404, 'Assistant record unavailable.')
    result = {k: (str(v) if v is not None and (k.endswith('_id') or k == 'id') else v.isoformat() if hasattr(v, 'isoformat') else v)
            for k, v in row.items() if k not in {'items', 'request_digest', 'role_instructions', 'lease_owner', 'lease_until', 'resume_context'}}
    if 'message' in row and 'mode' in row:
        result['name']=row['message'].split('\n',1)[0][:100]
    return result


def project(key):
    with connect() as conn:
        return public(get_row(conn, 'projects', key))


def conversation(conn, key, lock=False):
    row = conn.execute('SELECT * FROM assistant_conversations WHERE id=%s' + (' FOR UPDATE' if lock else ''), (key,)).fetchone()
    if not row:
        raise Problem(404, 'Conversation unavailable.')
    get_row(conn, 'projects', row['project'])
    return row


def new_conversation(key, title):
    with connect() as conn:
        get_row(conn, 'projects', key)
        return safe(conn.execute('INSERT INTO assistant_conversations(id,project,title) VALUES (%s,%s,%s) RETURNING *',
                                (uuid4(), key, title)).fetchone())


def conversations(key):
    project(key)
    with connect() as conn:
        return [safe(r) for r in conn.execute('SELECT * FROM assistant_conversations WHERE project=%s ORDER BY updated_at DESC,id', (key,))]


def transcript(key):
    with connect() as conn:
        row = conversation(conn, key)
        return {**safe(row), 'messages': [safe(r) for r in conn.execute('SELECT * FROM assistant_messages WHERE conversation_id=%s ORDER BY created_at,id', (key,))],
                'runs': [safe(r) for r in conn.execute('SELECT * FROM assistant_runs WHERE conversation_id=%s ORDER BY created_at,id', (key,))]}


def run_row(conn, key, lock=False):
    row = conn.execute('SELECT * FROM assistant_runs WHERE id=%s' + (' FOR UPDATE' if lock else ''), (key,)).fetchone()
    if not row:
        raise Problem(404, 'Run unavailable.')
    get_row(conn, 'projects', row['project'])
    return row


def get_run(key):
    with connect() as conn:
        return safe(run_row(conn, key))


def project_runs(key):
    project(key)
    with connect() as conn:
        return [safe(r) for r in conn.execute('SELECT * FROM assistant_runs WHERE project=%s ORDER BY created_at DESC LIMIT 100', (key,))]


def event(conn, key, name, payload):
    conn.execute('SELECT id FROM assistant_runs WHERE id=%s FOR UPDATE', (key,))
    return conn.execute('''INSERT INTO assistant_events(run_id,seq,type,payload)
        SELECT %s,COALESCE(MAX(seq),0)+1,%s,%s FROM assistant_events WHERE run_id=%s RETURNING seq''',
        (key, name, Jsonb(payload), key)).fetchone()['seq']


def emit(key, name, payload):
    with connect() as conn:
        event(conn, key, name, payload)


def events(key, after):
    with connect() as conn:
        row = run_row(conn, key)
        return {'run': safe(row), 'events': [safe(e) for e in conn.execute(
            'SELECT * FROM assistant_events WHERE run_id=%s AND seq>%s ORDER BY seq LIMIT 500', (key, after))]}


def board_state(conn, row, status, note):
    board = get_row(conn, 'runs', row['board_run_id'])
    mutate(conn, 'runs', 'Updated', 'InApp Assistant', {'status': status, 'note': note}, board['id'], board['revision'])


def update(key, status=None, step=None, **values):
    allowed = {'error', 'restore_point', 'checks', 'changed_files', 'cancelled'}
    if set(values) - allowed:
        raise ValueError('Unsupported run fields.')
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        row = run_row(conn, key, True)
        fields = dict(values)
        if status: fields['status'] = status
        if step: fields['last_confirmed_step'] = step
        cols = ','.join(f'{k}=%s' for k in fields)
        args = [Jsonb(v) if isinstance(v, (list, dict)) else v for v in fields.values()]
        if fields:
            conn.execute(f'UPDATE assistant_runs SET {cols},updated_at=now() WHERE id=%s', (*args, key))
        row = run_row(conn, key)
        note = row['last_confirmed_step'] + (': ' + row['error'] if row['error'] else '')
        note += '\nRun details: #project/' + row['project'] + '/assistant?run=' + str(key)
        board_state(conn, row, row['status'], note)
        event(conn, key, 'run.' + row['status'].lower().replace(' ', '_'), {'status': row['status'], 'last_confirmed_step': row['last_confirmed_step'], 'error': row['error']})
        return safe(row)


def require_scope(conn, row):
    if row['mode'] != 'Edit': return
    ticket = get_row(conn, 'tickets', row['ticket_id'])
    if ticket['project'] != row['project']:
        raise Problem(422, 'The ticket must belong to this project.')
    reviews.sync_project(conn, row['project'], 'InApp Assistant')
    reviews.require_ready(conn, row['ticket_id'])


def create_run(conversation_id, payload, checkout_key='', workspace_config=''):
    data = payload.model_dump(mode='json')
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        chat = conversation(conn, conversation_id, True)
        prior = conn.execute('SELECT * FROM assistant_runs WHERE conversation_id=%s AND request_id=%s', (conversation_id, payload.request_id)).fetchone()
        if prior:
            if prior['request_digest'] != digest: raise Problem(409, 'This request was already used with different content.')
            return safe(prior)
        if conn.execute("SELECT 1 FROM assistant_runs WHERE conversation_id=%s AND status IN ('Queued','Running')", (conversation_id,)).fetchone():
            raise Problem(409, 'Wait for this conversation’s current run, or start another conversation.')
        role = get_row(conn, 'roles', payload.role_id) if payload.role_id else None
        if role and role['project'] != chat['project']:
            raise Problem(422, 'Choose a role from this project.')
        data.update(project=chat['project'])
        require_scope(conn, {'mode': payload.mode, 'ticket_id': payload.ticket_id, 'project': chat['project']})
        run_id = uuid4()
        board = mutate(conn, 'runs', 'Created', 'InApp Assistant', {'name': payload.message[:100], 'project': chat['project'],
            'ticket': payload.ticket_id, 'agent': 'InApp Assistant', 'status': 'Queued', 'mode': payload.mode,
            'note': 'Request saved. Run details: #project/' + chat['project'] + '/assistant?run=' + str(run_id)})
        row = conn.execute('''INSERT INTO assistant_runs(id,conversation_id,project,request_id,request_digest,board_run_id,ticket_id,model,mode,
            role_id,role_name,role_instructions,status,message,checkout_key,workspace_config)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Queued',%s,%s,%s) RETURNING *''',
            (run_id, conversation_id, chat['project'], payload.request_id, digest, board['id'], payload.ticket_id, payload.model, payload.mode,
             payload.role_id, role['data']['name'] if role else '', role['data'].get('instructions', '') if role else '',
             payload.message, checkout_key, workspace_config)).fetchone()
        conn.execute("INSERT INTO assistant_messages(id,conversation_id,run_id,role,content) VALUES (%s,%s,%s,'user',%s)", (uuid4(), conversation_id, run_id, payload.message))
        conn.execute("UPDATE assistant_conversations SET title=CASE WHEN title='New conversation' THEN %s ELSE title END,updated_at=now() WHERE id=%s", (payload.message[:80],conversation_id))
        event(conn, run_id, 'run.queued', {'status': 'Queued', 'role_name': row['role_name']})
        return safe(row)


def candidate():
    with connect() as conn:
        return conn.execute("""SELECT r.* FROM assistant_runs r WHERE r.status='Queued' AND NOT r.cancelled
            AND NOT EXISTS(SELECT 1 FROM assistant_runs a WHERE a.id<>r.id AND
                ((a.status='Running' AND a.conversation_id=r.conversation_id) OR
                (r.mode='Edit' AND a.mode='Edit' AND (a.checkout_key=r.checkout_key OR starts_with(a.checkout_key,r.checkout_key||'/') OR starts_with(r.checkout_key,a.checkout_key||'/')) AND
                 (a.status='Running' OR (a.status IN ('Waiting for input','Blocked') AND a.restore_point IS NOT NULL) OR EXISTS(SELECT 1 FROM assistant_tool_attempts t WHERE t.run_id=a.id AND t.state IN ('started','uncertain'))))))
            ORDER BY r.created_at LIMIT 1""").fetchone()


def defer_queued(key,error):
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        row=run_row(conn,key,True)
        if row['status']!='Queued' or row['cancelled']: return
        conn.execute("UPDATE assistant_runs SET status='Waiting for input',error=%s,last_confirmed_step='File execution not started',updated_at=now() WHERE id=%s",(error,key))
        board_state(conn,row,'Waiting for input','File execution not started: '+error)
        event(conn,key,'run.waiting_for_input',{'status':'Waiting for input','error':error,'last_confirmed_step':'File execution not started'})


def claim(owner, candidate_id=None):
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        row = conn.execute("""SELECT r.* FROM assistant_runs r WHERE r.status='Queued' AND NOT r.cancelled AND (%s::uuid IS NULL OR r.id=%s)
            AND NOT EXISTS(SELECT 1 FROM assistant_runs a WHERE a.id<>r.id AND
                ((a.status='Running' AND a.conversation_id=r.conversation_id) OR
                (r.mode='Edit' AND a.mode='Edit' AND (a.checkout_key=r.checkout_key OR starts_with(a.checkout_key,r.checkout_key||'/') OR starts_with(r.checkout_key,a.checkout_key||'/')) AND
                 (a.status='Running' OR (a.status IN ('Waiting for input','Blocked') AND a.restore_point IS NOT NULL) OR EXISTS(SELECT 1 FROM assistant_tool_attempts t WHERE t.run_id=a.id AND t.state IN ('started','uncertain'))))))
            ORDER BY r.created_at FOR UPDATE SKIP LOCKED LIMIT 1""",(candidate_id,candidate_id)).fetchone()
        if not row: return None
        # Lock a canonical folder across processes. In-DB Running rows retain ownership until reconciliation.
        conn.execute("UPDATE assistant_runs SET status='Running',lease_owner=%s,lease_until=now()+interval '90 seconds',updated_at=now() WHERE id=%s", (owner, row['id']))
        return row


def heartbeat(key, owner):
    with connect() as conn:
        conn.execute("UPDATE assistant_runs SET lease_until=now()+interval '90 seconds' WHERE id=%s AND lease_owner=%s AND status='Running'", (key, owner))


def recover_expired():
    with connect() as conn:
        keys = [r['id'] for r in conn.execute("SELECT id FROM assistant_runs WHERE status='Running' AND lease_until<now()")]
    for key in keys:
        with connect() as conn:
            conn.execute("UPDATE assistant_tool_attempts SET state='uncertain',updated_at=now() WHERE run_id=%s AND state='started'", (key,))
        update(key, 'Waiting for input', error='Execution was interrupted. Review the last confirmed step before continuing or restoring.')


def tool_start(key, name, inputs):
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        row = run_row(conn, key, True)
        if inputs.get('workspace_config'):
            desired=conn.execute('SELECT config_id FROM assistant_execution_configuration').fetchone()
            if desired and desired['config_id']!=inputs['workspace_config']:
                raise Problem(409,'Local execution setup changed before this operation started.')
        if row['cancelled']: raise Problem(409, 'Cancellation requested.')
        if row['status'] != 'Running': raise Problem(409, 'Run paused. Review its current status.')
        if get_row(conn, 'runs', row['board_run_id'])['data']['status'] != 'Running':
            raise Problem(409, 'Requirements changed. Review current scope before continuing.')
        require_scope(conn, row)
        op = uuid4()
        conn.execute("INSERT INTO assistant_tool_attempts(id,run_id,name,input_digest,state,inputs) VALUES (%s,%s,%s,%s,'started',%s)",
                     (op, key, name, hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),Jsonb(inputs)))
        event(conn, key, 'tool.started', {'operation': str(op), 'name': name})
        return str(op)


def tool_finish(key, op, name, result, failed=False):
    with connect() as conn:
        run_row(conn, key, True)
        conn.execute('UPDATE assistant_tool_attempts SET state=%s,result=%s,updated_at=now() WHERE id=%s AND run_id=%s', ('failed' if failed else 'finished', Jsonb(result), op, key))
        event(conn, key, 'tool.finished', {'operation': op, 'name': name, 'result': result})
        conn.execute('UPDATE assistant_runs SET last_confirmed_step=%s,updated_at=now() WHERE id=%s', ('Finished ' + name, key))


def uncertain(key):
    with connect() as conn:
        return bool(conn.execute("SELECT 1 FROM assistant_tool_attempts WHERE run_id=%s AND state IN ('started','uncertain')", (key,)).fetchone())


def assert_active(key):
    with connect() as conn:
        row=run_row(conn,key,True)
        if row['cancelled']: raise Problem(409,'Cancellation requested. No new action may start.')
        if row['status']!='Running': raise Problem(409,'Run is paused.')
        require_scope(conn,row)
        return row


def finish(key, output, items, status='Completed', step='Confirmed response and evidence saved', error='', ticket_done=False):
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        row = run_row(conn, key, True)
        if row['cancelled']:
            pending=conn.execute("SELECT 1 FROM assistant_tool_attempts WHERE run_id=%s AND state IN ('started','uncertain')",(key,)).fetchone()
            status='Waiting for input' if pending else 'Cancelled'
            error='Cancellation interrupted a tool. Review its outcome.' if pending else ''
        if ticket_done and status=='Completed' and not row['cancelled']:
            require_scope(conn,row)
            ticket=get_row(conn,'tickets',row['ticket_id'])
            mutate(conn,'tickets','Updated','InApp Assistant',{'status':'Done'},ticket['id'],ticket['revision'])
        board_state(conn,row,status,step+('\n'+error if error else '')+'\nRun details: #project/'+row['project']+'/assistant?run='+str(key))
        existing=conn.execute("SELECT id FROM assistant_messages WHERE run_id=%s AND role='assistant'",(key,)).fetchone()
        if existing:
            conn.execute('UPDATE assistant_messages SET content=%s WHERE id=%s',(output,existing['id']))
        else:
            conn.execute("INSERT INTO assistant_messages(id,conversation_id,run_id,role,content) VALUES (%s,%s,%s,'assistant',%s)", (uuid4(), row['conversation_id'], key, output))
        conn.execute('UPDATE assistant_conversations SET items=%s,updated_at=now() WHERE id=%s', (Jsonb(items), row['conversation_id']))
        conn.execute('UPDATE assistant_runs SET status=%s,last_confirmed_step=%s,error=%s,updated_at=now() WHERE id=%s',(status,step,error,key))
        event(conn,key,'run.'+status.lower().replace(' ','_'),{'status':status,'last_confirmed_step':step,'error':error})
        return safe(run_row(conn,key))


def input_items(key):
    with connect() as conn:
        row = run_row(conn, key)
        chat = conversation(conn, row['conversation_id'])
        return chat['items'] + [{'role':'user','content':row.get('resume_context') or row['message']}]


def cancel(key):
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        row=run_row(conn,key,True)
        if row['status'] in TERMINAL: return safe(row)
        status='Cancelled' if row['status']=='Queued' else row['status']
        conn.execute('UPDATE assistant_runs SET cancelled=true,status=%s,updated_at=now() WHERE id=%s',(status,key))
        board_state(conn,row,status,'Cancellation requested; an active tool must settle before recovery.')
        event(conn,key,'run.cancel_requested',{'status':status})
        return safe(run_row(conn,key))


def resume(key):
    row=get_run(key)
    if row['status'] not in {'Waiting for input','Blocked','Failed'}:
        raise Problem(409, 'Only paused or failed runs can continue.')
    if uncertain(key):
        raise Problem(409, 'A tool outcome is uncertain. Inspect files and use Restore; it cannot be repeated automatically.')
    # A new model continuation gets confirmed journal evidence and never replays an operation.
    with connect() as conn:
        confirmed=conn.execute("SELECT name,state,result FROM assistant_tool_attempts WHERE run_id=%s ORDER BY created_at",(key,)).fetchall()
        continuation='Continue the original request from confirmed results only. Do not repeat finished writes. Original request: '+row['message']
        continuation+='\nConfirmed tool journal: '+json.dumps(confirmed,default=str)[:20000]
        conn.execute("UPDATE assistant_runs SET resume_context=%s WHERE id=%s", (continuation,key))
    return update(key, 'Queued', 'Continuation queued', cancelled=False, error='')


def pending_attempts(key):
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT id,name,inputs FROM assistant_tool_attempts WHERE run_id=%s AND state IN ('started','uncertain') ORDER BY created_at",(key,))]


def ticket_started(row):
    if row['mode']!='Edit': return
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        require_scope(conn,row)
        ticket=get_row(conn,'tickets',row['ticket_id'])
        if ticket['data']['status']=='Planned':
            mutate(conn,'tickets','Updated','InApp Assistant',{'status':'In progress'},ticket['id'],ticket['revision'])


def ticket_reopened(row):
    if not row['ticket_id']: return
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        ticket=get_row(conn,'tickets',row['ticket_id'])
        if ticket['data']['status']=='Done':
            mutate(conn,'tickets','Updated','InApp Assistant',{'status':'In progress'},ticket['id'],ticket['revision'])


def last_tool_error(key):
    with connect() as conn:
        row=conn.execute("SELECT result FROM assistant_tool_attempts WHERE run_id=%s AND state='failed' ORDER BY updated_at DESC LIMIT 1",(key,)).fetchone()
        return row['result'].get('error') if row and isinstance(row['result'],dict) else None
