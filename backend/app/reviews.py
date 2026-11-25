"""Durable impact reviews shared by the browser and native MCP clients.

The server enforces coverage and freshness. People/agents supply semantic judgment.
Local clients are trusted. Agents record user decisions with conversation evidence;
they must not make the user's scope decision themselves.
"""
import hashlib
import json
from typing import Literal
from uuid import uuid4

from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .db import connect

CORE_TYPES = {'product-vision', 'user-story', 'architecture-topic', 'design-topic', 'screen-inventory'}
READY = {'Ready', 'Confirmed'}


class Finding(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    document_id: str = Field(min_length=1)
    outcome: Literal['No update needed', 'Update required']
    reason: str = Field(min_length=1, max_length=4000)


class Assessment(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    conclusion: Literal['Within scope', 'Scope change', 'Unclear']
    rationale: str = Field(min_length=1, max_length=8000)
    findings: list[Finding] = Field(max_length=400)


def problem(status, message):
    from .store import Problem
    raise Problem(status, message)


def fields(kind, data):
    keys = ('description', 'content', 'document_type', 'source_documents', 'tags') if kind == 'documents' else (
        'name', 'description', 'documents', 'tags', 'work_type', 'execution_role')
    result = {key: data.get(key, [] if key in ('documents', 'source_documents', 'tags') else '') for key in keys}
    for key in ('documents', 'source_documents', 'tags'):
        if key in result:
            result[key] = sorted(result[key])
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def tracked(doc, baselines):
    return doc['id'] in baselines or (doc['data'].get('document_type') not in ('review-report', 'review-evidence')
        and doc['data']['name'].strip().lower() != 'tag catalog')


def snapshot(conn, subject):
    rows = conn.execute("SELECT * FROM records WHERE project=%s AND kind='documents' AND NOT deleted ORDER BY id",
                        (subject['project'],)).fetchall()
    baselines = {r['document_id']: r['snapshot'] for r in conn.execute(
        'SELECT b.* FROM scope_baselines b JOIN records r ON r.id=b.document_id WHERE r.project=%s', (subject['project'],))}
    docs = {r['id']: r for r in rows if tracked(r, baselines)}
    data = subject['data']
    chosen = set(data.get('documents' if subject['kind'] == 'tickets' else 'source_documents', [])) & docs.keys()
    chosen.update(r['id'] for r in rows if r['id'] in docs and set(data.get('tags', [])) & set(r['data'].get('tags', [])))
    has_context = bool(chosen)
    if subject['kind'] == 'documents':
        chosen.add(subject['id'])
    # Document impact follows both directions. Ticket scope follows source ancestors.
    while True:
        expanded = chosen | {key for key in docs for source in docs[key]['data'].get('source_documents', [])
                             if subject['kind'] == 'documents' and source in chosen}
        expanded |= {source for key in chosen if key in docs for source in docs[key]['data'].get('source_documents', []) if source in docs}
        if expanded == chosen:
            break
        chosen = expanded
    if not has_context and len(chosen) <= (1 if subject['kind'] == 'documents' else 0):
        chosen.update(key for key, r in docs.items() if r['data'].get('document_type') in CORE_TYPES)

    def item(row):
        content = fields(row['kind'], row['data'])
        return dict(id=row['id'], kind=row['kind'], name=row['data']['name'], revision=row['revision'],
                    fingerprint=digest(content), fields=content)

    target = item(subject)
    documents = [{**item(docs[key]), 'baseline': baselines.get(key)} for key in sorted(chosen) if key in docs]
    value = dict(subject=target, documents=documents, missing_context=subject['kind'] == 'tickets' and not has_context)
    signature = digest([target['fingerprint'], [(d['id'], d['fingerprint']) for d in documents], value['missing_context']])
    return value, signature


def log(conn, row, actor, action, changes):
    conn.execute("""INSERT INTO activity(project,actor,action,kind,record,name,changes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""", (row['project'], actor, action,
        row['snapshot']['subject']['kind'], row['subject'], row['snapshot']['subject']['name'], Jsonb(changes)))


def current(conn, subject):
    return conn.execute('SELECT * FROM change_reviews WHERE subject=%s AND NOT superseded', (subject,)).fetchone()


def new_review(conn, subject, value, signature, actor, request, operation='Edit'):
    conn.execute('UPDATE change_reviews SET superseded=true,revision=revision+1,updated_at=clock_timestamp() WHERE subject=%s AND NOT superseded', (subject['id'],))
    row = conn.execute("""INSERT INTO change_reviews(id,project,subject,review_type,operation,request,signature,snapshot)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""", ('RV-'+uuid4().hex[:12], subject['project'], subject['id'],
          'Document impact' if subject['kind'] == 'documents' else 'Ticket scope', operation, request, signature, Jsonb(value))).fetchone()
    log(conn, row, actor, 'Review requested', [['Review', None, row['review_type']], ['Reason', None, request]])
    return row


def sync_project(conn, project, actor='AgentBoard'):
    baselines = {r['document_id'] for r in conn.execute('SELECT b.document_id FROM scope_baselines b JOIN records r ON r.id=b.document_id WHERE r.project=%s', (project,))}
    subjects = conn.execute("SELECT * FROM records WHERE project=%s AND kind IN ('documents','tickets') AND NOT deleted ORDER BY id", (project,)).fetchall()
    for subject in subjects:
        if subject['kind'] == 'documents' and not tracked(subject, baselines):
            continue
        old = current(conn, subject['id'])
        if not old and subject['kind'] == 'tickets' and subject['data'].get('status') == 'Done':
            continue  # Preserve historical completion; reopening it requires a check.
        value, signature = snapshot(conn, subject)
        if not old or old['signature'] != signature:
            reason = old['request'] if old else 'Check the saved requirements and related documents.'
            if old:
                reason = 'Requirements or related documents changed. ' + old['request'][-2000:]
            new_review(conn, subject, value, signature, actor, reason, old['operation'] if old else 'Edit')
    hold_runs(conn, project)


def execution_ready(conn, row):
    if not row or row['status'] not in READY or row['operation'] != 'Edit' or row['snapshot']['missing_context']:
        return False
    return all((review := current(conn, doc['id'])) and review['status'] in READY and review['operation'] == 'Edit'
               for doc in row['snapshot']['documents'])


def hold_runs(conn, project):
    for run in conn.execute("SELECT * FROM records WHERE project=%s AND kind='runs' AND NOT deleted AND data->>'status'='Running'", (project,)).fetchall():
        if run['data'].get('mode', 'Edit') != 'Edit' or execution_ready(conn, current(conn, run['data'].get('ticket', ''))):
            continue
        data = {**run['data'], 'status': 'Waiting for input'}
        conn.execute('UPDATE records SET data=%s,revision=revision+1 WHERE id=%s', (Jsonb(data), run['id']))
        conn.execute("""INSERT INTO activity(project,actor,action,kind,record,name,changes)
            VALUES (%s,'AgentBoard','Review hold','runs',%s,%s,%s)""", (project, run['id'], data['name'],
            Jsonb([['status', 'Running', 'Waiting for input'], ['Review reason', None, 'Requirements need a current review. External agents must pause editing.']])))


def initialize():
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        for project in conn.execute("SELECT id FROM records WHERE kind='projects' AND NOT deleted").fetchall():
            sync_project(conn, project['id'])


def public(row):
    return {key: value.isoformat() if key in ('created_at', 'updated_at') else value for key, value in row.items()}


def list_reviews(conn, project=None):
    return [public(row) for row in conn.execute("""SELECT c.* FROM change_reviews c JOIN records r ON r.id=c.subject
        WHERE NOT r.deleted AND (%s::text IS NULL OR c.project=%s) ORDER BY c.created_at DESC,c.id""", (project, project))]


def start(actor, kind, key, revision, request, operation='Edit'):
    from .store import get_row
    if kind not in ('documents', 'tickets') or operation not in ('Edit', 'Delete') or (kind == 'tickets' and operation == 'Delete'):
        problem(422, 'Choose a document impact or ticket scope review.')
    if not request.strip() or len(request) > 8000:
        problem(422, 'Describe the requested change in 1 to 8000 characters.')
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        subject = get_row(conn, kind, key)
        if subject['revision'] != revision:
            problem(409, 'This record changed. Reload before requesting a review.')
        value, signature = snapshot(conn, subject)
        old = current(conn, key)
        if old and old['signature'] == signature and old['request'] == request.strip() and old['operation'] == operation:
            return public(old)
        row = new_review(conn, subject, value, signature, actor, request.strip(), operation)
        hold_runs(conn, subject['project'])
        return public(row)


def load_current(conn, key, revision):
    row = conn.execute('SELECT * FROM change_reviews WHERE id=%s', (key,)).fetchone()
    if not row:
        problem(404, 'This review is unavailable.')
    if row['superseded'] or row['revision'] != revision:
        problem(409, 'This review changed. Reload the current review before continuing.')
    subject = conn.execute('SELECT * FROM records WHERE id=%s AND NOT deleted', (row['subject'],)).fetchone()
    if not subject or snapshot(conn, subject)[1] != row['signature']:
        problem(409, 'The reviewed requirements changed. Read the latest review.')
    return row


def baseline(conn, row):
    if row['review_type'] == 'Document impact' and row['operation'] != 'Delete':
        conn.execute('''INSERT INTO scope_baselines(document_id,snapshot,review_id) VALUES (%s,%s,%s)
            ON CONFLICT(document_id) DO UPDATE SET snapshot=excluded.snapshot,review_id=excluded.review_id''',
            (row['subject'], Jsonb(row['snapshot']['subject']), row['id']))


def submit(actor, key, revision, assessment):
    try:
        data = Assessment.model_validate(assessment)
    except ValidationError as err:
        problem(422, str(err))
    if not data.rationale.strip() or any(not item.reason.strip() for item in data.findings):
        problem(422, 'Explain the decision and each document finding.')
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        row = load_current(conn, key, revision)
        if row['status'] in ('Awaiting confirmation', 'Confirmed', 'Declined'):
            problem(409, 'Start a new review to replace a scope-change decision.')
        expected = {doc['id'] for doc in row['snapshot']['documents']}
        actual = [item.document_id for item in data.findings]
        if len(actual) != len(set(actual)) or set(actual) != expected:
            problem(422, 'Give one finding for every document in this review, with no duplicates or extra documents.')
        if data.conclusion == 'Within scope' and row['snapshot']['missing_context']:
            problem(422, 'Link relevant Context documents or matching project tags before completing the scope check.')
        if row['operation'] == 'Delete' and data.conclusion != 'Scope change':
            problem(422, 'Removing a requirements document needs scope-change confirmation.')
        required = {item['document_id'] for item in row['findings'] if item['outcome'] == 'Update required'}
        if any(item.document_id in required and item.outcome == 'No update needed' for item in data.findings):
            problem(409, 'A required document update is still unchanged. Update the document and assess the refreshed review, or start a new review explaining a revised finding.')
        status = ('Awaiting confirmation' if data.conclusion == 'Scope change' else 'Unclear' if data.conclusion == 'Unclear'
                  else 'Needs updates' if any(item.outcome == 'Update required' for item in data.findings) else 'Ready')
        same_confirmation = (data.conclusion == row['conclusion'] == 'Scope change' and row['confirmed_by']
                             and data.rationale.strip() == row['rationale'])
        if same_confirmation:
            status = 'Needs updates' if any(item.outcome == 'Update required' for item in data.findings) else 'Confirmed'
        saved = conn.execute('''UPDATE change_reviews SET status=%s,conclusion=%s,rationale=%s,findings=%s,
            reviewer=%s,confirmed_by=%s,confirmation_note=%s,revision=revision+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *''',
            (status, data.conclusion, data.rationale.strip(), Jsonb([item.model_dump() for item in data.findings]), actor,
             None if status == 'Awaiting confirmation' else row['confirmed_by'],
             None if status == 'Awaiting confirmation' else row['confirmation_note'], key)).fetchone()
        if status == 'Ready':
            baseline(conn, saved)
        names = {doc['id']: doc['name'] for doc in row['snapshot']['documents']}
        def readable(items):
            return [f"{names.get(item['document_id'], 'Document')}: {item['outcome']} — {item['reason']}" for item in items]
        log(conn, saved, actor, 'Review assessed', [['Review result', row['status'], status],
            ['Checked documents', None, [f"{doc['name']} (revision {doc['revision']})" for doc in row['snapshot']['documents']]],
            ['Rationale', row['rationale'], saved['rationale']], ['Document findings', readable(row['findings']), readable(saved['findings'])]])
        hold_runs(conn, row['project'])
        return public(saved)


def confirm(key, revision, accept, note, recorder='Human'):
    if not isinstance(accept, bool) or not note.strip() or len(note) > 8000:
        problem(422, 'Explain the scope decision in 1 to 8000 characters.')
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(625016)')
        row = load_current(conn, key, revision)
        if row['status'] != 'Awaiting confirmation':
            problem(409, 'Only a proposed scope change needs confirmation.')
        status = 'Declined' if not accept else 'Needs updates' if any(f['outcome'] == 'Update required' for f in row['findings']) else 'Confirmed'
        decided_by = 'Human' if recorder == 'Human' else 'User via ' + recorder
        saved = conn.execute('''UPDATE change_reviews SET status=%s,confirmed_by=%s,confirmation_note=%s,
             revision=revision+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *''', (status, decided_by, note.strip(), key)).fetchone()
        if status == 'Confirmed':
            baseline(conn, saved)
        log(conn, saved, recorder, 'Scope decision', [['Review result', row['status'], status], ['Scope decision', None, note.strip()], ['Decision by', None, decided_by]])
        return public(saved)


def require_ready(conn, key, deletion=False):
    row = current(conn, key)
    if not row or row['status'] not in READY or (row['operation'] == 'Delete') != deletion:
        problem(409, 'Ask your agent to check the linked documents and ticket scope first. Findings are logged in Runs & activity.')
    if deletion and row['status'] != 'Confirmed':
        problem(409, 'Confirm the document removal scope change with your agent first.')
    if row['review_type'] == 'Ticket scope':
        if row['snapshot']['missing_context']:
            problem(409, 'Link Context documents or matching project tags and complete the scope check before implementation.')
        for doc in row['snapshot']['documents']:
            review = current(conn, doc['id'])
            if not review or review['status'] not in READY or review['operation'] != 'Edit':
                problem(409, f"Ask your agent to check document impact before implementation: {doc['name']}. Findings are logged in Runs & activity.")
    return row
