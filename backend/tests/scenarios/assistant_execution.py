"""Explicit smoke scenario against a generated executor project, never user code.

Run only with AGENTBOARD_EXECUTOR_FIXTURE_PROJECT pointing at a prepared Git
fixture containing index.js, test.js, and npm build/test scripts.
"""
import asyncio
from contextlib import nullcontext
import json
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

from agents import RunContextWrapper
from tests import test_contracts as fixtures
from app import assistant, assistant_store as store
from app.assistant_provider import CredentialStore


class ExecutorRuntimeSmoke(unittest.TestCase):
    create=fixtures.WorkspaceIntegration.create
    finish_reviews=fixtures.WorkspaceIntegration.finish_reviews

    def setUp(self):
        if not os.environ.get('AGENTBOARD_EXECUTOR_FIXTURE_PROJECT'):
            raise RuntimeError('Select the generated fixture project explicitly; never point this scenario at user code.')
        self.enterContext(patch.dict(os.environ,AGENTBOARD_ASSISTANT_WORKER='0'))
        fixtures.WorkspaceIntegration.setUp(self)
        if os.environ.get('AGENTBOARD_EXECUTOR_LIVE_SMOKE')!='1':
            self.enterContext(patch.object(assistant,'credentials',CredentialStore(environment_key='fixture-only-not-a-real-provider-key')))

    def test_reviewed_edit_build_test_evidence_commit_and_restore(self):
        p=self.create('projects',name='Generated executor acceptance',checkout_path=os.environ['AGENTBOARD_EXECUTOR_FIXTURE_PROJECT'])
        m=self.create('milestones',name='Generated acceptance',project=p['id'])
        d=self.create('documents',name='Agreed fixture task',project=p['id'],content='Update index.js to return 2 and update test.js to expect 2. Run the declared npm build and test scripts, save evidence, and commit only these changes.')
        role=self.create('roles',name='Backend Programmer',project=p['id'],instructions='Implement only the agreed fixture task. Verify commands and evidence.')
        ticket=self.create('tickets',name='Update fixture value',project=p['id'],milestone=m['id'],documents=[d['id']])
        self.finish_reviews(p['id'])
        chat=self.http.post('/api/assistant/projects/'+p['id']+'/conversations',json={}).json()
        response=self.http.post('/api/assistant/conversations/'+chat['id']+'/runs',json={'request_id':str(uuid4()),'message':'Update index.js to return 2, update test.js to expect 2. Read the two files first, then use write_file for only these two paths. Run npm run build and npm test sequentially with run_check. Limit source edits to index.js and test.js. Save the required verification evidence and commit only these two verified changes. Do not change package.json, create unrelated tickets/documents, or delegate. Give a short final result.','model':'gpt-6-luna','mode':'Edit','ticket_id':ticket['id'],'role_id':role['id']})
        self.assertEqual(response.status_code,201,response.text)
        row=store.claim('fixture-smoke')
        async def fake_provider(model,items,instructions,tools,**_kwargs):
            if not tools:
                data=json.loads(items[0]['content'])
                if data.get('type')=='completion':
                    return {'output_text':json.dumps({'complete':True,'rationale':'The generated task changed only the two agreed files and both declared checks passed.'}),'items':items}
                assessment={'conclusion':'Within scope','rationale':'The request exactly matches the agreed generated fixture task.','findings':[{'document_id':doc['id'],'outcome':'No update needed','reason':'The saved fixture agreement explicitly covers the value change and checks.'} for doc in data['review_snapshot']['documents']]}
                return {'output_text':json.dumps(assessment),'items':items}
            by_name={tool.name:tool for tool in tools}
            async def call(name,arguments):
                tool=by_name[name]
                ctx=RunContextWrapper(context=None)
                ctx.tool_name=name
                encoded=json.dumps(arguments)
                ctx._function_tool_arguments=tool.on_invoke_tool.prepare_arguments(encoded,name)
                return await tool.on_invoke_tool(ctx,encoded)
            await call('write_file',{'path':'index.js','content':'module.exports = () => 2;\n'})
            await call('write_file',{'path':'test.js','content':"const {test}=require('node:test'); const assert=require('node:assert'); test('value',()=>assert.equal(require('./index')(),2));\n"})
            await call('run_check',{'argv':['npm','run','build']})
            await call('run_check',{'argv':['npm','test']})
            return {'output_text':'Fixture changed. Build and test passed; evidence saved.','items':items+[{'role':'assistant','content':'Fixture changed. Build and test passed.'}]}
        execution_context=nullcontext() if os.environ.get('AGENTBOARD_EXECUTOR_LIVE_SMOKE')=='1' else patch.object(assistant.provider,'execute',fake_provider)
        with execution_context:
            asyncio.run(assistant.Runtime().execute(row))
        saved=store.get_run(response.json()['id'])
        # Simulate an explicit Continue choice after a provider interruption.
        # Never accept scope changes or replay an uncertain tool in this harness.
        if os.environ.get('AGENTBOARD_EXECUTOR_LIVE_SMOKE')=='1':
            for _ in range(2):
                transient=any(text in saved.get('error','') for text in ('could not be reached','did not respond in time','step limit'))
                if saved['status']!='Waiting for input' or store.uncertain(saved['id']) or not transient: break
                continued=self.http.post('/api/assistant/runs/'+saved['id']+'/continue')
                self.assertEqual(continued.status_code,200,continued.text)
                claimed=store.claim('fixture-explicit-continue')
                self.assertIsNotNone(claimed)
                asyncio.run(assistant.Runtime().execute(claimed))
                saved=store.get_run(saved['id'])
        self.assertEqual(saved['status'],'Completed',saved)
        self.assertEqual(saved['role_name'],'Backend Programmer')
        self.assertTrue({('npm','run','build'),('npm','test')}.issubset({tuple(c['command']) for c in saved['checks']}))
        self.assertTrue(all(c['passed'] for c in saved['checks']))
        state=self.http.get('/api/workspace?view=export').json()
        completed=next(t for t in state['tickets'] if t['id']==ticket['id'])
        self.assertEqual(completed['status'],'Done')
        self.assertTrue(completed['output_documents'])
        preview=self.http.post('/api/assistant/runs/'+saved['id']+'/restore-preview')
        self.assertEqual(preview.status_code,200,preview.text)
        self.assertFalse(preview.json()['conflicts'])
        restored=self.http.post('/api/assistant/runs/'+saved['id']+'/restore')
        self.assertEqual(restored.status_code,200,restored.text)
        self.assertEqual(restored.json()['status'],'Cancelled')
        print(json.dumps({'scope_preflight':'passed','provider':'live OpenAI' if os.environ.get('AGENTBOARD_EXECUTOR_LIVE_SMOKE')=='1' else 'deterministic fixture','role_snapshot':'queried and applied','file_tools':'verified executor','npm_build':'passed','npm_test':'passed','ticket_evidence':'linked','run_only_commit':'verified','selective_restore':'passed'}))


if __name__=='__main__': unittest.main(verbosity=2)
