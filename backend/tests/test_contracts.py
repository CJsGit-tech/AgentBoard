import asyncio
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import psycopg
from psycopg import sql
from fastapi.testclient import TestClient
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic import ValidationError

from app.api import app
from app.db import connect
from app.models import Ticket


class DataRules(unittest.TestCase):
    def test_ticket_requires_milestone_and_valid_date(self):
        for values in ({"due":"2026-02-30","milestone":"M"}, {"due":""}, {"milestone":" "}):
            with self.assertRaises(ValidationError):
                Ticket.model_validate(dict(name="Ticket",project="P",**values))


class WorkspaceIntegration(unittest.TestCase):
    def setUp(self):
        # Only this unique disposable database is touched.
        self.dbname = "ab_test_"+uuid4().hex
        self.admin = psycopg.connect(host="db", dbname="postgres", user="agentboard",
                                     password=Path("/run/secrets/db_password").read_text().strip(), autocommit=True)
        self.addCleanup(self.admin.close)
        identifier = sql.Identifier(self.dbname)
        self.admin.execute(sql.SQL("CREATE DATABASE {}").format(identifier))
        self.addCleanup(self.admin.execute, sql.SQL("DROP DATABASE {}").format(identifier))
        self.enterContext(patch.dict(os.environ, AGENTBOARD_DATABASE=self.dbname))
        self.http = self.enterContext(TestClient(app, base_url="http://localhost", headers={"X-AgentBoard-UI":"1"}))

    def create(self, kind, **fields):
        result=self.http.post(f"/api/{kind}",json=fields)
        self.assertEqual(result.status_code,201,result.text)
        return result.json()

    def finish_reviews(self, project):
        reviews = self.http.get('/api/workspace').json()['reviews']
        for review in reviews:
            if review['project'] != project or review['superseded'] or review['status'] != 'Pending':
                continue
            result = self.http.post('/api/reviews/'+review['id']+'/assess', json={
                'revision': review['revision'], 'assessment': {'conclusion': 'Within scope',
                'rationale': 'Fixture requirements match the agreed test scenario.', 'findings': [
                    {'document_id': doc['id'], 'outcome':'No update needed', 'reason':'The scenario explicitly covers this behavior.'}
                    for doc in review['snapshot']['documents']]}})
            self.assertEqual(result.status_code, 200, result.text)

    def approve_removal(self, doc):
        review = self.http.post('/api/reviews/start/documents/'+doc['id'], json={
            'revision':doc['revision'], 'request':'Remove this requirements document.', 'operation':'Delete'}).json()
        assessed = self.http.post('/api/reviews/'+review['id']+'/assess', json={'revision':review['revision'],
            'assessment':{'conclusion':'Scope change', 'rationale':'Remove the documented scope.', 'findings':[
                {'document_id':d['id'], 'outcome':'No update needed', 'reason':'Removal reviewed.'} for d in review['snapshot']['documents']]}}).json()
        result = self.http.post('/api/reviews/'+review['id']+'/confirm', json={'revision':assessed['revision'],
            'accept':True,'note':'Confirmed removal in this test.'})
        self.assertEqual(result.status_code, 200, result.text)

    def test_mcp_ui_share_state_and_history(self):
        async def run():
            transport=StdioTransport("python",["-m","app.mcp_server","--client","Codex"],
                                     env={"AGENTBOARD_DATABASE":self.dbname},cwd="/srv")
            async with Client(transport) as client:
                tools = {tool.name for tool in await client.list_tools()}
                self.assertTrue({"record_schema","create_record","list_records","get_record","update_record",
                                 "delete_record","restore_record","list_activity"} <= tools)
                p=self.create("projects",name="Integration")
                m=self.create("milestones",name="Milestone",project=p["id"])
                doc=self.create('documents',name='Requirements',project=p['id'],content='Shared ticket behavior')
                t=self.create("tickets",name="Shared ticket",project=p["id"],milestone=m["id"],documents=[doc['id']])
                self.finish_reviews(p['id'])
                change=await client.call_tool("update_record",dict(kind="tickets",id=t["id"],revision=1,changes={"status":"Done"}))
                self.assertFalse(change.is_error)
                state=self.http.get("/api/workspace").json()
                self.assertEqual(state["tickets"][0]["status"],"Done")
                self.assertEqual(state["activity"][0]["actor"],"Codex")
                self.assertIn(["status","Planned","Done"],state["activity"][0]["changes"])
                stale=self.http.patch("/api/tickets/"+t["id"],json={"revision":1,"changes":{"name":"late"}})
                self.assertEqual(stale.status_code,409)
                failed=self.http.delete("/api/milestones/"+m["id"],params={"revision":1})
                self.assertEqual(failed.status_code,409)
                await client.call_tool("delete_record",dict(kind="tickets",id=t["id"],revision=2))
                self.assertEqual(len(self.http.get("/api/workspace").json()["trash"]),1)
                restored=self.http.post("/api/tickets/"+t["id"]+"/restore",json={"revision":3})
                self.assertEqual(restored.json()["revision"],4)
                fetched=await client.call_tool("get_record",dict(kind="tickets",id=t["id"]))
                self.assertIn("Shared ticket",str(fetched.content))
                other=self.create("projects",name="Other")
                invalid=self.http.post("/api/tickets",json={"name":"Mismatch","milestone":m["id"],"project":other["id"]})
                self.assertEqual(invalid.status_code,422)
        asyncio.run(run())

    def test_conditional_refresh(self):
        response = self.http.get("/api/workspace")
        headers = {"if-none-match": response.headers["etag"]}
        self.assertEqual(self.http.get("/api/workspace", headers=headers).status_code, 304)
        self.create("projects", name="Fresh workspace")
        changed = self.http.get("/api/workspace", headers=headers)
        self.assertEqual(changed.status_code, 200)
        self.assertNotEqual(changed.headers["etag"], response.headers["etag"])

    def test_browser_boundary(self):
        self.assertEqual(self.http.get("/api/workspace",headers={"origin":"http://unrelated.invalid"}).status_code,403)
        self.assertEqual(self.http.get("/api/workspace",headers={"host":"unrelated.invalid"}).status_code,400)
        self.assertEqual(self.http.get("/api/workspace",headers={"X-AgentBoard-UI":""}).status_code,403)

    def test_permanent_project_removal_requires_current_confirmation(self):
        project = self.create("projects", name="Old project")["id"]
        milestone = self.create("milestones", name="Milestone", project=project)["id"]
        role = self.create("roles", name="Designer", project=project)["id"]
        inventory = self.create("documents", name="Mockups", project=project,
                                document_type="screen-inventory", content="First screen")["id"]
        ticket = self.create("tickets", name="Ticket", project=project,
                             milestone=milestone, documents=[inventory], role=role)["id"]
        self.finish_reviews(project)
        run = self.create("runs", name="Report", project=project, ticket=ticket,
                          agent="Codex", status="Completed")["id"]
        self.assertEqual(self.http.delete(f"/api/runs/{run}", params={"revision":1}).status_code, 200)
        with connect() as conn:
            conn.execute("INSERT INTO visual_assets VALUES (%s,%s,%s,%s)",
                         (inventory, "screen.png", "test-digest", b"preview bytes"))

        path = f"/api/projects/{project}"
        preview = self.http.get(path + "/deletion-preview").json()
        self.assertEqual(preview["counts"], dict(milestones=1, tickets=1, roles=1, documents=1, runs=1))
        self.assertEqual(preview["previews"], 1)
        confirmation = {key: preview[key] for key in ("revision", "activity_version")}
        wrong = self.http.post(path + "/purge", json={**confirmation, "confirmation":"old project"})
        self.assertEqual(wrong.status_code, 422)
        confirmation["confirmation"] = preview["name"]
        self.create("tickets", name="New activity", project=project, milestone=milestone)
        self.assertEqual(self.http.post(path + "/purge", json=confirmation).status_code, 409)

        # Add a newer event in another project so deleting the target cannot change MAX(seq).
        other = self.create("projects", name="Keep me")["id"]
        other_milestone = self.create("milestones", name="Keep this too", project=other)["id"]
        before = self.http.get("/api/workspace")
        latest = self.http.get(path + "/deletion-preview").json()
        confirmation["activity_version"] = latest["activity_version"]
        self.assertEqual(self.http.post(path + "/purge", json=confirmation,
                                        headers={"X-AgentBoard-UI":""}).status_code, 403)
        removed = self.http.post(path + "/purge", json=confirmation)
        self.assertEqual(removed.status_code, 204, removed.text)
        self.assertEqual(self.http.post(path + "/purge", json=confirmation).status_code, 404)
        self.assertEqual(self.http.get(f"/api/visuals/{inventory}/screen.png").status_code, 404)
        with connect() as conn:
            for query, key in (
                ("SELECT COUNT(*) AS total FROM records WHERE project=%s", project),
                ("SELECT COUNT(*) AS total FROM activity WHERE project=%s", project),
                ("SELECT COUNT(*) AS total FROM visual_assets WHERE document_id=%s", inventory),
            ):
                self.assertEqual(conn.execute(query, (key,)).fetchone()["total"], 0)
        after = self.http.get("/api/workspace", headers={"if-none-match":before.headers["etag"]})
        self.assertEqual(after.status_code, 200)
        state = after.json()
        self.assertEqual([row["id"] for row in state["projects"]], [other])
        self.assertEqual([row["id"] for row in state["milestones"]], [other_milestone])
        self.assertEqual(state["trash"], [])

    def test_agentbuild_document_visual_ticket_handoff(self):
        import base64
        from hashlib import sha256

        project = self.create("projects", name="Handoff", checkout_path="/example/Handoff")["id"]
        milestone = self.create("milestones", name="First release", project=project)["id"]
        brief = self.create("documents", name="Product Vision", document_type="product-vision",
                            project=project, content="State: Draft")
        duplicate = self.http.post("/api/documents", json={**{"project":project, "content":"Draft"},
            "name":"Product Brief", "document_type":"product-vision"})
        self.assertEqual(duplicate.status_code, 422)
        vocabulary = "## checkout\nLabel: Checkout\nMeaning: Ordering\nState: Active"
        catalog = self.create("documents", name="Tag Catalog", project=project, content=vocabulary)
        inventory = self.create("documents", name="Visuals — checkout", project=project,
                                document_type="screen-inventory", content="Checkout screen", tags=["checkout"])
        bug = self.create("tickets", name="Save button", project=project, milestone=milestone,
                          work_type="BUG", execution_role="FE", documents=[brief["id"]], tags=["checkout"])
        self.finish_reviews(project)
        # Build a PNG with checked chunk lengths and CRCs.
        import struct
        import zlib
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1,1,8,2,0,0,0)) +
               chunk(b"IDAT", zlib.compress(bytes(4))) + chunk(b"IEND", b""))
        encoded = base64.b64encode(png).decode()
        async def handoff():
            for label in ("Claude", "Codex"):
                transport = StdioTransport("python", ["-m","app.mcp_server","--client",label],
                                           env={"AGENTBOARD_DATABASE":self.dbname}, cwd="/srv")
                async with Client(transport) as client:
                    for kind, record in (("documents", inventory), ("tickets", bug)):
                        result = await client.call_tool("list_records", {"kind":kind, "project":project, "tag":"checkout"})
                        self.assertEqual([r["id"] for r in result.data], [record["id"]])
                    if label == "Claude":
                        args = dict(document_id=inventory["id"], revision=1, filename="checkout.png", png_base64=encoded)
                        uploaded = (await client.call_tool("attach_visual", args)).data
                        self.assertEqual(uploaded["previews"][0]["digest"], sha256(png).hexdigest())
                        self.assertEqual(uploaded["revision"], 2)
                        replay = (await client.call_tool("attach_visual", {**args, "revision":2})).data
                        self.assertEqual(replay["revision"], 2)
                    else:
                        linked = (await client.call_tool("update_record", dict(kind="tickets", id=bug["id"],
                            revision=1, changes={"documents":[brief["id"], inventory["id"]]}))).data
                        self.assertEqual(linked["record_path"], "/#tickets/"+bug["id"])
        asyncio.run(handoff())
        url = "/api/visuals/" + inventory["id"] + "/checkout.png"
        self.assertEqual(self.http.get(url).content, png)
        self.assertEqual(self.http.get(url, headers={"X-AgentBoard-UI":""}).status_code, 403)
        state = self.http.get("/api/workspace").json()
        self.assertEqual(state["tickets"][0]["documents"], [brief["id"], inventory["id"]])
        backend_bug = self.create("tickets", name="Order endpoint", project=project, milestone=milestone,
                                  execution_role="BE", work_type="BUG", tags=["checkout"])
        self.assertEqual(backend_bug["execution_role"], "BE")
        retired = self.http.patch("/api/documents/"+catalog["id"], json={"revision":1,
                                  "changes":{"content":vocabulary.replace("Active", "Retired")}})
        self.assertEqual(retired.status_code, 200)
        rejected = self.http.post("/api/tickets", json=dict(name="Another", project=project,
                                  milestone=milestone, tags=["checkout"]))
        self.assertEqual(rejected.status_code, 422)

    def test_design_canvas_publications(self):
        from base64 import b64encode
        from app.canvas import publish
        from app.store import Problem

        project = self.create("projects", name="Design")["id"]
        doc = self.create("documents", name="Design Profile", project=project,
                          document_type="design-topic", content="Workspace screens")
        source = self.create("documents", name="UserScreens", project=project,
                             document_type="screen-inventory", content="Original screens")
        self.finish_reviews(project)
        metadata = {"change_note": "Initial canvas", "sources": [{"document_id": source["id"], "revision": 1}]}
        files = {"gallery.html": b64encode(b"<main>First version</main>").decode(),
                 "assets/board.js": b64encode(b"console.log('sample')").decode()}
        first = publish("Codex", doc["id"], doc["revision"], files, **metadata)
        initial = first["canvas_versions"][0]
        retry = publish("Codex", doc["id"], first["revision"], files, **metadata)
        self.assertEqual(retry["revision"], first["revision"])
        for rejected, revision, code in [({**files, "../private.js": "YQ=="}, first["revision"], 422),
                                         (files, doc["revision"], 409)]:
            with self.assertRaises(Problem) as failure:
                publish("Codex", doc["id"], revision, rejected, **metadata)
            self.assertEqual(failure.exception.status, code)
        second = publish("Claude", doc["id"], first["revision"], {**files, "gallery.html": "djI="},
                         **{**metadata, "change_note":"Added a screen"})
        self.assertEqual([v["version"] for v in second["canvas_versions"]], [2, 1])
        self.assertEqual(initial["publisher"], "Codex")
        self.assertEqual(initial["change_note"], "Initial canvas")
        self.assertEqual(initial["sources"], [{"document_id": source["id"], "revision": 1, "name": "UserScreens"}])
        self.http.patch("/api/documents/" + source["id"], json={"revision": 1, "changes":{"name":"Updated screens"}})
        unchanged = self.http.get("/api/workspace").json()["documents"]
        historical = next(record for record in unchanged if record["id"] == doc["id"])["canvas_versions"][-1]
        self.assertEqual(historical["sources"][0]["name"], "UserScreens")
        with self.assertRaises(Problem) as stale:
            publish("Codex", doc["id"], second["revision"], files, **metadata)
        self.assertEqual(stale.exception.status, 409)
        other = self.create("projects", name="Other design")["id"]
        outside = self.create("documents", name="External", project=other, content="Other project")
        with self.assertRaises(Problem) as mismatch:
            publish("Codex", doc["id"], second["revision"], files, "Invalid source",
                    [{"document_id": outside["id"], "revision": 1}])
        self.assertEqual(mismatch.exception.status, 422)
        path = "/canvas-content/" + initial["asset_key"] + "/gallery.html"
        original = self.http.get(path)
        self.assertEqual(original.content, b"<main>First version</main>")
        self.assertIn("sandbox allow-scripts", original.headers["content-security-policy"])
        self.assertNotIn("allow-same-origin", original.headers["content-security-policy"])
        self.approve_removal({**doc, 'revision':second['revision']})
        self.assertEqual(self.http.delete("/api/documents/" + doc["id"],
                         params={"revision":second["revision"]}).status_code, 200)
        self.assertEqual(self.http.get(path).status_code, 404)

    def review_fixture(self):
        p = self.create('projects', name='Review rules')['id']
        m = self.create('milestones', name='Delivery', project=p)['id']
        d = self.create('documents', name='Scope', project=p, document_type='user-story', content='Users can save a ticket.')
        t = self.create('tickets', name='Save a ticket', description='Implement the documented Save action.',
                        project=p, milestone=m, documents=[d['id']])
        return p, m, d, t

    def current_review(self, key):
        return next(r for r in self.http.get('/api/workspace').json()['reviews'] if r['subject'] == key and not r['superseded'])

    def assess(self, review, conclusion='Within scope', update=None, **extra):
        return self.http.post('/api/reviews/'+review['id']+'/assess', json={
            'revision':review['revision'], 'assessment':{'conclusion':conclusion,
            'rationale':'Story Save action covers this work. Scope change would add comments.',
            'findings':[{'document_id':d['id'], 'outcome':'Update required' if d['id'] == update else 'No update needed',
                        'reason':'Checked the Save action story and recorded request.'} for d in review['snapshot']['documents']], **extra}})

    def test_reviews_required_without_asking_for_within_scope_confirmation(self):
        p, m, doc, ticket = self.review_fixture()
        path = '/api/tickets/'+ticket['id']
        self.assertEqual(self.http.patch(path,json={'revision':1,'changes':{'status':'In progress'}}).status_code,409)
        self.assertEqual(self.http.post('/api/tickets',json={'name':'Bypass','project':p,'milestone':m,'status':'Done'}).status_code,409)
        self.assertEqual(self.http.post('/api/runs',json={'name':'Bypass','project':p,'ticket':ticket['id'],
            'agent':'Codex','status':'Running'}).status_code,409)
        self.finish_reviews(p)
        review = self.current_review(ticket['id'])
        self.assertEqual(review['status'],'Ready')
        self.assertEqual(self.http.post('/api/reviews/'+review['id']+'/confirm',json={
            'revision':review['revision'],'accept':True,'note':'Unnecessary'}).status_code,409)
        self.assertEqual(self.http.patch(path,json={'revision':1,'changes':{'status':'In progress'}}).status_code,200)
        self.create('runs',name='Implementation',project=p,ticket=ticket['id'],agent='Codex',status='Running')
        read = self.create('runs',name='Inspection',project=p,agent='Claude',status='Running',mode='Read only')
        self.assertEqual(read['mode'],'Read only')

    def test_scope_change_needs_human_decision_and_stale_decisions_fail(self):
        p, _, doc, ticket = self.review_fixture()
        self.finish_reviews(p)
        review = self.http.post('/api/reviews/start/tickets/'+ticket['id'],json={
            'revision':1,'request':'Add comments to the ticket.'}).json()
        assessed = self.assess(review,'Scope change').json()
        self.assertEqual(assessed['status'],'Awaiting confirmation')
        self.assertEqual(self.http.patch('/api/tickets/'+ticket['id'],json={'revision':1,'changes':{'status':'In progress'}}).status_code,409)
        confirmed = self.http.post('/api/reviews/'+review['id']+'/confirm',json={
            'revision':assessed['revision'],'accept':True,'note':'Add comments to this release.'})
        self.assertEqual(confirmed.status_code,200,confirmed.text)
        self.assertEqual(confirmed.json()['confirmed_by'],'Human')
        self.assertEqual(self.http.patch('/api/tickets/'+ticket['id'],json={'revision':1,'changes':{'status':'In progress'}}).status_code,200)
        change = self.http.patch('/api/documents/'+doc['id'],json={'revision':1,'changes':{'content':'Users can save tickets and add comments.'}})
        self.assertEqual(change.status_code,200)
        self.assertTrue(next(r for r in self.http.get('/api/workspace').json()['reviews'] if r['id'] == review['id'])['superseded'])
        self.assertEqual(self.http.post('/api/reviews/'+review['id']+'/confirm',json={
            'revision':confirmed.json()['revision'],'accept':True,'note':'Stale approval'}).status_code,409)
        self.assertEqual(self.current_review(ticket['id'])['status'],'Pending')
        self.assertEqual(self.assess(self.current_review(ticket['id']),confirmed_by='Human').status_code,422)

    def test_required_document_updates_cannot_be_cleared_by_scope_confirmation(self):
        p, _, doc, ticket = self.review_fixture()
        self.finish_reviews(p)
        started = self.http.post('/api/reviews/start/tickets/'+ticket['id'],json={'revision':1,'request':'Add comments.'}).json()
        assessed = self.assess(started,'Scope change',update=doc['id']).json()
        result = self.http.post('/api/reviews/'+started['id']+'/confirm',json={
            'revision':assessed['revision'],'accept':True,'note':'Agreed, update the story first.'})
        self.assertEqual(result.json()['status'],'Needs updates')
        repeated = self.assess(result.json(),'Scope change',update=doc['id'])
        self.assertEqual(repeated.json()['status'],'Needs updates')
        self.assertEqual(self.assess(repeated.json(),'Within scope').status_code,409)
        self.assertEqual(self.http.patch('/api/tickets/'+ticket['id'],json={'revision':1,'changes':{'status':'Done'}}).status_code,409)
        self.http.patch('/api/documents/'+doc['id'],json={'revision':1,'changes':{'content':'Save tickets and add comments.'}})
        self.finish_reviews(p)
        self.assertEqual(self.http.patch('/api/tickets/'+ticket['id'],json={'revision':1,'changes':{'status':'In progress'}}).status_code,200)

    def test_dependencies_tags_and_changed_content_invalidate_only_affected_work(self):
        p, m, doc, ticket = self.review_fixture()
        dependent = self.create('documents',name='Screen rules',project=p,document_type='screen-inventory',
                                content='Save button',source_documents=[doc['id']])
        other = self.create('documents',name='Other feature',project=p,content='Unrelated feature requirements')
        unrelated = self.create('tickets',name='Other work',project=p,milestone=m,documents=[other['id']])
        self.finish_reviews(p)
        old = self.current_review(ticket['id'])
        other_review = self.current_review(unrelated['id'])
        run = self.create('runs',name='Editing',project=p,ticket=ticket['id'],agent='Codex',status='Running')
        self.http.patch('/api/documents/'+doc['id'],json={'revision':1,'changes':{'name':'Renamed scope'}})
        self.assertEqual(self.current_review(ticket['id'])['id'],old['id'])
        self.http.patch('/api/documents/'+doc['id'],json={'revision':2,'changes':{'content':'Changed Save behavior'}})
        self.assertNotEqual(self.current_review(ticket['id'])['id'],old['id'])
        self.assertEqual(self.current_review(unrelated['id'])['id'],other_review['id'])
        self.assertEqual(self.current_review(dependent['id'])['status'],'Pending')
        changed_doc = self.current_review(doc['id'])
        own_snapshot = next(d for d in changed_doc['snapshot']['documents'] if d['id'] == doc['id'])
        self.assertEqual(own_snapshot['baseline']['fields']['content'],'Users can save a ticket.')
        runs = self.http.get('/api/workspace').json()['runs']
        self.assertEqual(next(r for r in runs if r['id'] == run['id'])['status'],'Waiting for input')
        # Cycles and cross-project source links cannot bypass relationship validation.
        self.assertEqual(self.http.patch('/api/documents/'+doc['id'],json={'revision':3,
            'changes':{'source_documents':[dependent['id']]}}).status_code,422)
        other_project = self.create('projects',name='Elsewhere')['id']
        external = self.create('documents',name='External scope',project=other_project,content='Other scope')
        self.assertEqual(self.http.patch('/api/documents/'+doc['id'],json={'revision':3,
            'changes':{'source_documents':[external['id']]}}).status_code,422)
        catalog = self.create('documents',name='Tag Catalog',project=p,content='## save\nState: Active')
        tagged = self.http.patch('/api/documents/'+doc['id'],json={'revision':3,'changes':{'tags':['save']}})
        self.assertEqual(tagged.status_code,200,tagged.text)
        tag_ticket = self.create('tickets',name='Tag related work',project=p,milestone=m,tags=['save'])
        tag_review = self.current_review(tag_ticket['id'])
        self.assertFalse(tag_review['snapshot']['missing_context'])
        self.assertIn(doc['id'],[d['id'] for d in tag_review['snapshot']['documents']])

    def test_review_coverage_missing_context_and_declined_scope(self):
        p, m, doc, ticket = self.review_fixture()
        pending = self.current_review(ticket['id'])
        self.assertEqual(self.assess(pending,findings=[]).status_code,422)
        missing = self.create('tickets',name='No context',project=p,milestone=m)
        self.assertEqual(self.assess(self.current_review(missing['id'])).status_code,422)
        changed = self.assess(pending,'Scope change').json()
        declined = self.http.post('/api/reviews/'+pending['id']+'/confirm',json={
            'revision':changed['revision'],'accept':False,'note':'Keep the current scope.'})
        self.assertEqual(declined.json()['status'],'Declined')
        self.assertEqual(self.http.patch('/api/tickets/'+ticket['id'],json={'revision':1,'changes':{'status':'In progress'}}).status_code,409)
        self.assertEqual(self.assess(declined.json()).status_code,409)

    def test_mcp_scope_decision_records_user_evidence_in_existing_activity(self):
        p, _, doc, ticket = self.review_fixture()
        self.finish_reviews(p)
        async def verify():
            transport=StdioTransport('python',['-m','app.mcp_server','--client','Claude'],env={'AGENTBOARD_DATABASE':self.dbname},cwd='/srv')
            async with Client(transport) as client:
                tool_names = {tool.name for tool in await client.list_tools()}
                self.assertIn('assess_change_review',tool_names)
                self.assertFalse(any('confirm' in name for name in tool_names))
                started = (await client.call_tool('start_change_review',{'kind':'tickets','id':ticket['id'],'revision':1,'request':'Add comments.'})).data
                assessment = {'conclusion':'Scope change','rationale':'Comments extend the saved Save-only story.',
                    'findings':[{'document_id':d['id'],'outcome':'No update needed','reason':'Reviewed comment impact.'} for d in started['snapshot']['documents']]}
                assessed = (await client.call_tool('assess_change_review',{'id':started['id'],'revision':started['revision'],'assessment':assessment})).data
                self.assertEqual(assessed['status'],'Awaiting confirmation')
                self.assertEqual(assessed['reviewer'],'Claude')
                result = await client.call_tool('update_record',{'kind':'tickets','id':ticket['id'],'revision':1,'changes':{'status':'In progress'}},raise_on_error=False)
                self.assertTrue(result.is_error)
                missing = await client.call_tool('record_user_scope_decision', {'id':started['id'],
                    'revision':assessed['revision'],'accept':True,'user_quote':' ',
                    'conversation_reference':'Current Claude chat'}, raise_on_error=False)
                self.assertTrue(missing.is_error)
                decided = (await client.call_tool('record_user_scope_decision', {'id':started['id'],
                    'revision':assessed['revision'],'accept':True,'user_quote':'Yes, add comments to tickets.',
                    'conversation_reference':'Current Claude chat, response to the comments proposal'})).data
                self.assertEqual(decided['status'],'Confirmed')
                self.assertEqual(decided['confirmed_by'],'User via Claude')
                activity = (await client.call_tool('list_activity',{'project':p,'record':ticket['id']})).data
                decision = next(row for row in activity if row['action']=='Scope decision')
                self.assertEqual(decision['actor'],'Claude')
                self.assertIn('Yes, add comments to tickets.',str(decision['changes']))
                stale = await client.call_tool('record_user_scope_decision', {'id':started['id'],
                    'revision':assessed['revision'],'accept':False,'user_quote':'Keep the current scope.',
                    'conversation_reference':'Current Claude chat'}, raise_on_error=False)
                self.assertTrue(stale.is_error)
        asyncio.run(verify())

    def test_document_removal_and_restore_have_separate_impact_checks(self):
        p = self.create('projects',name='Document lifecycle')['id']
        doc = self.create('documents',name='Scope',project=p,content='Original requirements')
        path = '/api/documents/'+doc['id']
        self.assertEqual(self.http.delete(path,params={'revision':1}).status_code,409)
        self.approve_removal(doc)
        self.assertEqual(self.http.delete(path,params={'revision':1}).status_code,200)
        restored = self.http.post(path+'/restore',json={'revision':2})
        self.assertEqual(restored.status_code,200,restored.text)
        review = self.current_review(doc['id'])
        self.assertEqual((review['operation'],review['status']),('Edit','Pending'))

    def test_packaged_history_import_keeps_reviews_pending_without_exposing_a_bypass(self):
        from app.sample import install
        self.assertEqual(install(),'Installed the two sample projects.')
        data = self.http.get('/api/workspace').json()
        self.assertEqual(len(data['projects']),2)
        self.assertTrue(any(t['status'] == 'Done' for t in data['tickets']))
        self.assertTrue(data['reviews'])
        self.assertTrue(all(review['status'] == 'Pending' for review in data['reviews']))
        self.assertFalse(any(run['status'] == 'Running' and run['mode'] == 'Edit' for run in data['runs']))
        project, milestone = data['projects'][0]['id'], data['milestones'][0]
        rejected = self.http.post('/api/tickets',json={'name':'Bypass import','project':milestone['project'],
            'milestone':milestone['id'],'historical_import':True,'status':'Done'})
        self.assertEqual(rejected.status_code,422)
        self.assertIn('skipped',install().lower())
