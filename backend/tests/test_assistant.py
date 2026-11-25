"""Contract tests run in disposable PostgreSQL databases; no provider calls."""
import asyncio
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from tests import test_contracts as fixtures
from app import assistant, assistant_store as store
from app.assistant_provider import CredentialStore
from app.db import connect


class AssistantIntegration(unittest.TestCase):
    setUp = fixtures.WorkspaceIntegration.setUp
    create = fixtures.WorkspaceIntegration.create
    finish_reviews = fixtures.WorkspaceIntegration.finish_reviews

    def setUp(self):
        self.enterContext(patch.dict(os.environ, AGENTBOARD_ASSISTANT_WORKER='0'))
        fixtures.WorkspaceIntegration.setUp(self)
        self.enterContext(patch.object(assistant,'credentials',CredentialStore(environment_key='test-not-a-real-provider-key')))
        self.project=self.create('projects',name='Assistant fixture')
        self.chat=self.http.post('/api/assistant/projects/'+self.project['id']+'/conversations',json={}).json()

    def send(self, **extra):
        data=dict(request_id=str(uuid4()),message='Explain the board',model=assistant.config()['models'][0]['id'],mode='Read only')
        data.update(extra)
        return self.http.post('/api/assistant/conversations/'+self.chat['id']+'/runs',json=data)

    def test_project_history_and_request_idempotency(self):
        request=str(uuid4())
        first=self.send(request_id=request)
        self.assertEqual(first.status_code,201,first.text)
        second=self.send(request_id=request)
        self.assertEqual(first.json()['id'],second.json()['id'])
        conflict=self.send(request_id=request,message='Different request')
        self.assertEqual(conflict.status_code,409)
        other=self.create('projects',name='Other project')
        self.assertEqual(self.http.get('/api/assistant/projects/'+other['id']+'/conversations').json(),[])
        transcript=self.http.get('/api/assistant/conversations/'+self.chat['id']).json()
        self.assertEqual(len(transcript['messages']),1)
        self.assertEqual(len(transcript['runs']),1)

    def test_mount_not_needed_for_chat_but_edit_is_rejected(self):
        with patch.object(assistant.workspace,'require_workspace',side_effect=AssertionError('Chat tried to mount')):
            result=self.send()
            self.assertEqual(result.status_code,201,result.text)
        result=self.send(mode='Edit')
        self.assertEqual(result.status_code,422)
        self.assertIn('reviewed ticket',result.text)

    def test_events_are_durable_and_replay_ordered(self):
        run=self.send().json()
        store.emit(run['id'],'fixture.step',{'step':'one'})
        store.emit(run['id'],'fixture.step',{'step':'two'})
        events=self.http.get('/api/assistant/runs/'+run['id']+'/events?after_seq=1').json()['events']
        self.assertEqual([e['seq'] for e in events],[2,3])
        self.assertEqual([e['payload']['step'] for e in events],['one','two'])

    def test_scope_and_cross_project_role_gates(self):
        other=self.create('projects',name='Other')
        role=self.create('roles',name='Other role',project=other['id'])
        result=self.send(role_id=role['id'])
        self.assertEqual(result.status_code,422)
        milestone=self.create('milestones',name='Work',project=self.project['id'])
        ticket=self.create('tickets',name='Pending',project=self.project['id'],milestone=milestone['id'])
        with patch.object(assistant.workspace,'require_workspace') as mount,patch.object(assistant.workspace,'execution_status',return_value={}):
            mount.return_value.path='/workspaces/project'
            self.assertEqual(self.send(mode='Edit',ticket_id=ticket['id']).status_code,409)

    def test_folder_queue_readonly_concurrency_and_cancel(self):
        # Durable claims serialize a conversation and edit roots while allowing a second project chat.
        one=self.send().json()
        other_chat=self.http.post('/api/assistant/projects/'+self.project['id']+'/conversations',json={}).json()
        other=self.http.post('/api/assistant/conversations/'+other_chat['id']+'/runs',json=dict(request_id=str(uuid4()),message='Parallel',model=assistant.config()['models'][0]['id'])).json()
        a=store.claim('fixture')
        b=store.claim('fixture')
        self.assertEqual({str(a['id']),str(b['id'])},{one['id'],other['id']})
        self.http.post('/api/assistant/runs/'+one['id']+'/cancel')
        self.assertTrue(store.get_run(one['id'])['cancelled'])
        # Simulate a lease lost during a tool: it must pause, not repeat a write.
        with connect() as conn:
            conn.execute("UPDATE assistant_runs SET lease_until=now()-interval '1 second' WHERE id=%s",(one['id'],))
            conn.execute("INSERT INTO assistant_tool_attempts(id,run_id,name,input_digest,state) VALUES(%s,%s,'write_file','fixture','started')",(uuid4(),one['id']))
        store.recover_expired()
        self.assertEqual(store.get_run(one['id'])['status'],'Waiting for input')
        self.assertEqual(self.http.post('/api/assistant/runs/'+one['id']+'/continue').status_code,409)

    def test_restart_keeps_chat_but_not_session_key(self):
        run=self.send().json()
        self.assertEqual(store.get_run(run['id'])['status'],'Queued')
        with patch.object(assistant,'credentials',CredentialStore(environment_key='')):
            config=self.http.get('/api/assistant/config').json()
            self.assertFalse(config['credential']['configured'])
            self.assertEqual(len(store.transcript(self.chat['id'])['messages']),1)

    def test_credential_validation_does_not_echo_secret(self):
        response=self.http.put('/api/assistant/credential',json={'api_key':'short-key'})
        self.assertEqual(response.status_code,422)
        self.assertNotIn('short-key',response.text)

    def test_fake_provider_runs_through_worker_without_network(self):
        run=self.send().json()
        async def fake(model_id,input_items,instructions,tools,on_event=None,cancel_requested=None):
            self.assertTrue(tools)
            return {'output_text':'Confirmed local fixture response.','items':input_items+[{'role':'assistant','content':'Confirmed local fixture response.'}]}
        with patch.object(assistant.provider,'execute',fake):
            row=store.claim('fixture')
            asyncio.run(assistant.Runtime().execute(row))
        saved=store.get_run(run['id'])
        self.assertEqual(saved['status'],'Completed',saved)
        transcript=store.transcript(self.chat['id'])
        self.assertEqual(transcript['messages'][-1]['role'],'assistant')
        workspace=self.http.get('/api/workspace').json()
        board=next(r for r in workspace['runs'] if r['id']==run['board_run_id'])
        self.assertEqual(board['assistant_run_id'],run['id'])
        override=self.http.patch('/api/runs/'+board['id'],json={'revision':board['revision'],'changes':{'status':'Failed'}})
        self.assertEqual(override.status_code,409)
        self.assertEqual(store.get_run(run['id'])['status'],'Completed')

    def test_cancelled_unknown_tool_keeps_review_hold(self):
        run=self.send().json()
        store.claim('fixture')
        store.update(run['id'],'Running','Worker started')
        op=store.tool_start(run['id'],'fixture_write',{'path':'a.txt'})
        store.cancel(run['id'])
        state=store.finish(run['id'],'Stopped safely.',[],status='Completed')
        self.assertEqual(state['status'],'Waiting for input')
        self.assertTrue(store.uncertain(run['id']))
        self.assertEqual(self.http.post('/api/assistant/runs/'+run['id']+'/continue').status_code,409)

    def test_answer_and_terminal_state_commit_atomically(self):
        run=self.send().json()
        store.claim('fixture')
        state=store.finish(run['id'],'Saved once.',[{'role':'assistant','content':'Saved once.'}])
        self.assertEqual(state['status'],'Completed')
        store.recover_expired()
        self.assertEqual(store.get_run(run['id'])['status'],'Completed')
        store.finish(run['id'],'Saved once.',[{'role':'assistant','content':'Saved once.'}])
        answers=[m for m in store.transcript(self.chat['id'])['messages'] if m['role']=='assistant']
        self.assertEqual(len(answers),1)

    def test_new_chat_scope_is_checked_before_any_snapshot_or_file_edit(self):
        import json
        from pathlib import Path
        from app.assistant_workspace import WorkspaceHandle
        doc=self.create('documents',name='Agreed scope',project=self.project['id'],content='The existing save button can be repaired.')
        milestone=self.create('milestones',name='Work',project=self.project['id'])
        ticket=self.create('tickets',name='Fix save button',project=self.project['id'],milestone=milestone['id'],documents=[doc['id']])
        self.finish_reviews(self.project['id'])
        handle=WorkspaceHandle(Path('/workspaces/project'),'/fixture','fixture')
        with patch.object(assistant.workspace,'require_workspace',return_value=handle),patch.object(assistant.workspace,'execution_status',return_value={'config_id':'fixture'}):
            result=self.send(mode='Edit',ticket_id=ticket['id'],message='Add a new payments feature.')
            self.assertEqual(result.status_code,201,result.text)
            row=store.claim('fixture')
            async def scope_check(*args,**kwargs):
                payload=json.loads(args[1][0]['content'])
                return {'output_text':json.dumps({'conclusion':'Scope change','rationale':'Payments adds behavior beyond the agreed save repair.','findings':[{'document_id':d['id'],'outcome':'No update needed','reason':'The old agreement is preserved until the user decides.'} for d in payload['review_snapshot']['documents']]}),'items':[]}
            with patch.object(assistant.provider,'execute',scope_check),patch.object(assistant.workspace,'snapshot') as snapshot:
                asyncio.run(assistant.Runtime().execute(row))
                snapshot.assert_not_called()
        saved=store.get_run(result.json()['id'])
        self.assertEqual(saved['status'],'Waiting for input',saved)
        checks=self.http.get('/api/workspace').json()['reviews']
        self.assertTrue(any(r['subject']==ticket['id'] and r['status']=='Awaiting confirmation' and not r['superseded'] for r in checks))

    def test_unready_queue_never_reports_running_and_cancel_is_preserved(self):
        run=self.send().json()
        self.assertEqual(str(store.candidate()['id']),run['id'])
        store.defer_queued(run['id'],'Selected folder became unavailable.')
        saved=store.get_run(run['id'])
        self.assertEqual(saved['status'],'Waiting for input')
        self.assertEqual(saved['last_confirmed_step'],'File execution not started')
        events=store.events(run['id'],0)['events']
        self.assertFalse(any(e['type']=='run.running' for e in events))
        # A cancellation that wins the queue race cannot be turned into a review hold.
        other=self.http.post('/api/assistant/projects/'+self.project['id']+'/conversations',json={}).json()
        response=self.http.post('/api/assistant/conversations/'+other['id']+'/runs',json={'request_id':str(uuid4()),'message':'Question','model':assistant.config()['models'][0]['id']})
        key=response.json()['id']
        store.cancel(key)
        store.defer_queued(key,'Folder unavailable')
        self.assertEqual(store.get_run(key)['status'],'Cancelled')

    def test_chat_ticket_proposal_links_back_without_file_access(self):
        import json
        from agents import RunContextWrapper
        doc=self.create('documents',name='Requirements',project=self.project['id'],content='Propose the requested task and check its scope before editing.')
        milestone=self.create('milestones',name='Work',project=self.project['id'])
        run=self.send(message='Create a planned repair ticket.').json()
        store.claim('fixture')
        store.update(run['id'],'Running','Worker started')
        tools=assistant.Runtime().tools(store.get_run(run['id']),store.project(self.project['id']))
        tool=next(t for t in tools if t.name=='propose_ticket')
        args=json.dumps({'name':'Requested repair','description':'Repair the agreed behavior.','milestone_id':milestone['id'],'document_ids':[doc['id']]})
        ctx=RunContextWrapper(None)
        ctx.tool_name=tool.name
        ctx._function_tool_arguments=tool.on_invoke_tool.prepare_arguments(args,tool.name)
        with patch.object(assistant.workspace,'require_workspace',side_effect=AssertionError('Board proposal requested a mount')):
            ticket=json.loads(asyncio.run(tool.on_invoke_tool(ctx,args)))
        saved=store.get_run(run['id'])
        self.assertEqual(saved['ticket_id'],ticket['id'])
        state=self.http.get('/api/workspace').json()
        board=next(r for r in state['runs'] if r['id']==run['board_run_id'])
        self.assertEqual(board['ticket'],ticket['id'])
        self.assertEqual(ticket['status'],'Planned')
