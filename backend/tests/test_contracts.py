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
from app.models import MODELS, Ticket


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
        reviews = self.http.get('/api/workspace?view=export').json()['reviews']
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
                state=self.http.get("/api/workspace?view=export").json()
                self.assertEqual(state["tickets"][0]["status"],"Done")
                self.assertEqual(state["activity"][0]["actor"],"Codex")
                self.assertIn(["status","Planned","Done"],state["activity"][0]["changes"])
                stale=self.http.patch("/api/tickets/"+t["id"],json={"revision":1,"changes":{"name":"late"}})
                self.assertEqual(stale.status_code,409)
                failed=self.http.delete("/api/milestones/"+m["id"],params={"revision":1})
                self.assertEqual(failed.status_code,409)
                await client.call_tool("delete_record",dict(kind="tickets",id=t["id"],revision=2))
                self.assertEqual(len(self.http.get("/api/workspace?view=export").json()["trash"]),1)
                restored=self.http.post("/api/tickets/"+t["id"]+"/restore",json={"revision":3})
                self.assertEqual(restored.json()["revision"],4)
                fetched=await client.call_tool("get_record",dict(kind="tickets",id=t["id"]))
                self.assertIn("Shared ticket",str(fetched.content))
                other=self.create("projects",name="Other")
                invalid=self.http.post("/api/tickets",json={"name":"Mismatch","milestone":m["id"],"project":other["id"]})
                self.assertEqual(invalid.status_code,422)
        asyncio.run(run())

    def test_project_kpi_targets_default_validate_and_check_revisions(self):
        project = self.create("projects", name="Targets")
        listed = next(row for row in self.http.get("/api/workspace?view=projects").json()["projects"] if row["id"] == project["id"])
        self.assertEqual((listed["target_completion"], listed["target_evidence"], listed["target_run_success"], listed["target_median_hours"]),
                         (100, 90, 95, 4.0))
        for changes in ({"target_evidence": 101}, {"target_completion": -1}, {"target_median_hours": 0}, {"target_run_success": "95"}):
            rejected = self.http.patch("/api/projects/" + project["id"], json={"revision": project["revision"], "changes": changes})
            self.assertEqual(rejected.status_code, 422, changes)
        saved = self.http.patch("/api/projects/" + project["id"], json={"revision": project["revision"],
                                "changes": {"target_evidence": 80, "target_median_hours": 2.5}})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual((saved.json()["target_evidence"], saved.json()["target_median_hours"]), (80, 2.5))
        stale = self.http.patch("/api/projects/" + project["id"], json={"revision": project["revision"], "changes": {"target_evidence": 70}})
        self.assertEqual(stale.status_code, 409)
        schema = MODELS["projects"].model_json_schema()["properties"]
        self.assertEqual((schema["target_evidence"]["minimum"], schema["target_evidence"]["maximum"], schema["target_median_hours"]["maximum"]), (0, 100, 720))

    def test_dashboard_and_portfolio_metrics_are_read_only_and_match_records(self):
        empty = self.create("projects", name="Empty metrics")
        metrics = self.http.get(f"/api/projects/{empty['id']}/metrics").json()
        self.assertEqual(metrics["tickets"]["total"], 0)
        self.assertEqual((metrics["completion"]["percent"], metrics["evidence_coverage"]["percent"], metrics["run_success"]["percent"],
                          metrics["median_hours_to_last_update"], metrics["runs_by_agent"]), (None, None, None, None, {}))
        self.assertEqual([d["count"] for d in metrics["done_per_day"]], [0] * 7)
        self.assertEqual(metrics["targets"]["target_evidence"], 90)

        project = self.create("projects", name="Metrics")
        milestone = self.create("milestones", name="M", project=project["id"])
        spec = self.create("documents", name="Spec", project=project["id"], content="Metrics behavior")
        proof = self.create("documents", name="Proof", project=project["id"], content="Evidence", document_type="review-evidence")
        shipped = self.create("tickets", name="Shipped", project=project["id"], milestone=milestone["id"], documents=[spec["id"]])
        self.create("tickets", name="Planned work", project=project["id"], milestone=milestone["id"], documents=[spec["id"]])
        self.finish_reviews(project["id"])
        done = self.http.patch("/api/tickets/" + shipped["id"], json={"revision": shipped["revision"],
                               "changes": {"status": "Done", "output_documents": [proof["id"]]}})
        self.assertEqual(done.status_code, 200, done.text)
        before = self.http.get("/api/workspace?view=export").json()["activity"]

        no_runs = self.http.get(f"/api/projects/{project['id']}/metrics").json()
        self.assertEqual(no_runs["tickets"]["statuses"], {"Done": 1, "In progress": 0, "Blocked": 0, "Planned": 1})
        self.assertEqual((no_runs["completion"]["percent"], no_runs["evidence_coverage"]["percent"]), (50.0, 100.0))
        self.assertIsNone(no_runs["run_success"]["percent"])
        self.assertEqual(sum(d["count"] for d in no_runs["done_per_day"]), 1)

        for status in ("Completed", "Failed", "Running"):
            self.create("runs", name="Run " + status, project=project["id"], agent="Codex", status=status, mode="Read only")
        with_runs = self.http.get(f"/api/projects/{project['id']}/metrics").json()
        self.assertEqual((with_runs["run_success"]["value"], with_runs["run_success"]["total"]), (1, 2))
        self.assertEqual(with_runs["runs_by_agent"]["Codex"]["total"], 3)

        portfolio = self.http.get("/api/portfolio").json()
        rows = {row["name"]: row for row in portfolio["projects"]}
        self.assertEqual((rows["Metrics"]["total"], rows["Metrics"]["open"], rows["Empty metrics"]["total"]), (2, 1, 0))
        self.assertEqual(rows["Metrics"]["runs_by_agent"]["Codex"]["statuses"], {"Completed": 1, "Failed": 1, "Running": 1})
        self.assertEqual(rows["Empty metrics"]["runs_by_agent"], {})
        self.assertEqual(self.http.get("/api/portfolio", params={"start": "2026-02-10", "end": "2026-02-01"}).status_code, 422)
        self.assertEqual(self.http.get("/api/projects/P-missing/metrics").status_code, 404)
        after = self.http.get("/api/workspace?view=export").json()["activity"]
        self.assertEqual(len(after), len(before) + 3)  # only the three run creations wrote activity

    def test_retired_unscoped_read_always_returns_a_reload_instruction(self):
        with patch("app.api.state") as full_export, patch("app.api.browser_workspace.browser_state") as scoped:
            for headers in ({}, {"if-none-match": '"workspace-v6-1-0"'}):
                response = self.http.get("/api/workspace", headers=headers)
                self.assertEqual(response.status_code, 410)
                self.assertIn("Reload this tab", response.json()["detail"])
                self.assertLess(len(response.content), 200)
                self.assertEqual(response.headers["cache-control"], "no-store")
            full_export.assert_not_called()
            scoped.assert_not_called()
        self.assertEqual(self.http.get("/api/workspace?view=export&project=P-test").status_code, 422)

    def test_explicit_full_export_supports_conditional_reads(self):
        response = self.http.get("/api/workspace?view=export")
        headers = {"if-none-match": response.headers["etag"]}
        self.assertEqual(self.http.get("/api/workspace?view=export", headers=headers).status_code, 304)
        self.create("projects", name="Fresh workspace")
        changed = self.http.get("/api/workspace?view=export", headers=headers)
        self.assertEqual(changed.status_code, 200)
        self.assertNotEqual(changed.headers["etag"], response.headers["etag"])

    def test_scoped_browser_reads_keep_review_snapshots_on_demand(self):
        project = self.create("projects", name="Optimization")["id"]
        other = self.create("projects", name="Other")["id"]
        milestone = self.create("milestones", name="First", project=project)["id"]
        doc = self.create("documents", name="Requirements", project=project, content="Original requirement")
        ticket = self.create("tickets", name="Scoped", project=project, milestone=milestone, documents=[doc["id"]])
        first = self.http.get("/api/workspace", params={"project": project})
        path = f"/api/projects/{project}/reviews/"
        compact = next(r for r in first.json()["reviews"] if r["subject"] == ticket["id"])
        self.assertNotIn("fields", compact["snapshot"]["documents"][0])
        self.assertNotIn("baseline", compact["snapshot"]["documents"][0])
        self.assertEqual([p["id"] for p in first.json()["projects"]], [project])
        self.assertEqual(self.http.get(f'/api/records/tickets/{ticket["id"]}/project').json(), {"project": project})
        self.assertEqual(self.http.get(f'/api/projects/{other}/reviews/{compact["id"]}').status_code, 404)

        changed = self.http.patch("/api/documents/" + doc["id"], json={
            "revision": doc["revision"], "changes": {"content": "Updated requirement"}})
        self.assertEqual(changed.status_code, 200)
        updated = self.http.get("/api/workspace", params={"project": project}, headers={"if-none-match": first.headers["etag"]})
        current = next(r for r in updated.json()["reviews"] if r["subject"] == ticket["id"])
        self.assertNotEqual(current["id"], compact["id"])
        review_pages = path.rstrip("/")
        history = self.http.get(review_pages, params={"subject": ticket["id"], "limit": 1}).json()
        self.assertEqual(history["items"][0]["id"], current["id"])
        self.assertNotIn("snapshot", history["items"][0])
        archive = self.http.get(review_pages, params={"subject": ticket["id"], "offset": history["next_offset"]}).json()
        self.assertEqual(archive["items"][0]["id"], compact["id"])
        self.assertIsNone(archive["next_offset"])
        self.assertEqual(self.http.get(f"/api/projects/{other}/reviews", params={"subject": ticket["id"]}).json()["items"], [])
        old = self.http.get(path + compact["id"]).json()
        self.assertTrue(old["superseded"])
        self.assertEqual(old["snapshot"]["documents"][0]["fields"]["content"], "Original requirement")
        self.assertFalse(any(row["superseded"] for row in updated.json()["reviews"]))
        headers = {"if-none-match": updated.headers["etag"]}
        self.create("milestones", name="Other project change", project=other)
        stable = self.http.get("/api/workspace", params={"project": project}, headers=headers)
        self.assertEqual((stable.status_code, stable.content), (304, b""))

        directory = self.http.get("/api/workspace?view=projects", headers=headers)
        summary = next(p["summary"] for p in directory.json()["projects"] if p["id"] == project)
        self.assertEqual((summary["statuses"]["Planned"], summary["milestones"], summary["documents"]), (1, 1, 1))
        for key in ("tickets", "documents", "activity", "reviews"):
            self.assertEqual(directory.json()[key], [])
        self.assertNotIn(b"Original requirement", directory.content)
        self.assertEqual(self.http.get("/api/workspace?view=projects",
                         headers={"if-none-match": directory.headers["etag"]}).status_code, 304)
        self.assertEqual(self.http.get("/api/workspace?view=projects&project=" + project).status_code, 422)

    def test_scoped_activity_keeps_filtered_history_across_pages_and_dashboard_events(self):
        project = self.create("projects", name="Timeline")["id"]
        other = self.create("projects", name="Other")["id"]
        milestone = self.create("milestones", name="Ship", project=project)["id"]
        ticket = self.create("tickets", name="Review evidence", project=project, milestone=milestone)
        for title in ("Review updated", "Review finalized"):
            reply = self.http.patch("/api/tickets/" + ticket["id"], json={
                "revision": ticket["revision"], "changes": {"name": title}})
            self.assertEqual(reply.status_code, 200)
            ticket = reply.json()
        path = f"/api/projects/{project}/activity"
        filters = {"record": ticket["id"], "kind": "tickets", "actor": "Human", "action": "Updated",
                   "search": "NAME", "limit": 1}
        page1 = self.http.get(path, params=filters).json()
        self.assertEqual(page1["items"][0]["name"], "Review finalized")
        self.assertEqual(page1["total"], 2)
        self.assertIn("Created", page1["facets"]["actions"])
        page2 = self.http.get(path, params={**filters, "before": page1["next_before"]}).json()
        self.assertEqual(page2["items"][0]["name"], "Review updated")
        self.assertNotEqual(page1["items"][0]["id"], page2["items"][0]["id"])
        self.assertEqual(page2["total"], 2)
        self.assertIsNone(page2["next_before"])
        self.assertEqual(self.http.get(f"/api/projects/{other}/activity", params=filters).json()["items"], [])
        self.assertEqual(self.http.get(path, params={**filters, "start":"2100-01-01T00:00:00Z"}).json()["total"], 0)
        self.assertEqual(self.http.get(path, params={"limit": 0}).status_code, 422)
        project_read = self.http.get("/api/workspace", params={"project": project}).json()
        self.assertEqual(project_read["activity_count"], self.http.get(path).json()["total"])
        self.assertEqual([e["changes"] for e in project_read["activity"]], [[["status", None, "Planned"]]])

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
        before = self.http.get("/api/workspace?view=export")
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
        after = self.http.get("/api/workspace?view=export", headers={"if-none-match":before.headers["etag"]})
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
        self.assertEqual(self.http.get(url, params={"v": sha256(png).hexdigest()}).content, png)
        self.assertEqual(self.http.get(url, params={"v": "f" * 64}).status_code, 404)
        self.assertEqual(self.http.get(url, headers={"X-AgentBoard-UI":""}).status_code, 403)
        state = self.http.get("/api/workspace?view=export").json()
        self.assertEqual(state["tickets"][0]["documents"], [brief["id"], inventory["id"]])
        screenshot = dict(kind="screenshot", document_id=inventory["id"], filename="checkout.png",
                          digest=sha256(png).hexdigest(), status="verified")
        proof = self.http.patch("/api/tickets/" + bug["id"], json={"revision": 2, "changes": {
            "output_documents": [inventory["id"]],
            "criteria": [{"id": "checkout-preview", "text": "Checkout matches the approved screen.",
                          "evidence_required": True, "evidence": [screenshot]}],
        }})
        self.assertEqual(proof.status_code, 200, proof.text)
        self.assertEqual(proof.json()["criteria"][0]["evidence"], [screenshot])
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
                         **{**metadata, "change_note":"Added a screen", "screen_count": 2})
        self.assertEqual([v["version"] for v in second["canvas_versions"]], [2, 1])
        self.assertEqual([v["screen_count"] for v in second["canvas_versions"]], [2, None])
        retry = publish("Claude", doc["id"], second["revision"], {**files, "gallery.html": "djI="},
                        **{**metadata, "change_note":"Added a screen", "screen_count": 2})
        self.assertEqual(retry["revision"], second["revision"])
        for invalid_count in (0, -1, "2", True):
            with self.assertRaises(Problem) as invalid:
                publish("Codex", doc["id"], second["revision"], files, **metadata, screen_count=invalid_count)
            self.assertEqual(invalid.exception.status, 422)
        second = publish("Claude", doc["id"], second["revision"], {**files, "gallery.html": "djI="},
                         **{**metadata, "change_note":"Added a screen", "screen_count": 3})
        self.assertEqual([v["screen_count"] for v in second["canvas_versions"]], [3, 2, None])
        self.assertEqual(initial["publisher"], "Codex")
        self.assertEqual(initial["change_note"], "Initial canvas")
        self.assertEqual(initial["sources"], [{"document_id": source["id"], "revision": 1, "name": "UserScreens"}])
        self.http.patch("/api/documents/" + source["id"], json={"revision": 1, "changes":{"name":"Updated screens"}})
        unchanged = self.http.get("/api/workspace?view=export").json()["documents"]
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
        self.assertEqual(original.headers["cache-control"], "private, no-cache")
        isolated = self.http.get(path, headers={"X-Canvas-Origin": "1"})
        policy = isolated.headers["content-security-policy"]
        self.assertIn("sandbox allow-scripts allow-forms allow-same-origin;", policy)
        self.assertIn("worker-src 'none'; frame-ancestors http://localhost:8080 ", policy)
        for blocked in ("/api/workspace?view=projects", "/healthz"):
            self.assertEqual(self.http.get(blocked, headers={"X-Canvas-Origin": "1"}).status_code, 404)
        self.assertEqual(self.http.get("/api/workspace?view=projects",
                                       headers={"Origin": "http://localhost:8081"}).status_code, 403)
        tag = original.headers["etag"]
        self.assertFalse(tag.startswith("W/"))
        from app.canvas import read_asset
        with patch("app.api.read_asset", wraps=read_asset) as read:
            head = self.http.head(path)
            self.assertEqual(head.status_code, 200)
            self.assertEqual(head.content, b"")
            for name in ("content-type", "content-length", "etag", "cache-control", "content-security-policy"):
                self.assertEqual(head.headers[name], original.headers[name])
            for validator in (tag, "*", f'"old", W/{tag}'):
                for method in ("HEAD", "GET"):
                    validated = self.http.request(method, path, headers={"If-None-Match": validator})
                    self.assertEqual(validated.status_code, 304)
                    self.assertEqual(validated.content, b"")
                    self.assertEqual(validated.headers["etag"], tag)
                    self.assertEqual(validated.headers["content-security-policy"], original.headers["content-security-policy"])
            self.assertTrue(all(not call.kwargs["include_content"] for call in read.call_args_list))
        script = self.http.get(path.replace("gallery.html", "assets/board.js"), headers={"If-None-Match": tag})
        newer = self.http.get(path.replace(initial["asset_key"], second["canvas_versions"][0]["asset_key"]),
                              headers={"If-None-Match": tag})
        for response in (script, newer):
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content)
            self.assertNotEqual(response.headers["etag"], tag)
        self.assertEqual(self.http.head(path.replace("gallery.html", "absent.js"),
                                        headers={"If-None-Match": "*"}).status_code, 404)
        self.approve_removal({**doc, 'revision':second['revision']})
        self.assertEqual(self.http.delete("/api/documents/" + doc["id"],
                         params={"revision":second["revision"]}).status_code, 200)
        self.assertEqual(self.http.get(path).status_code, 404)
        for method in ("GET", "HEAD"):
            unavailable = self.http.request(method, path, headers={"If-None-Match": tag})
            self.assertEqual(unavailable.status_code, 404)
            self.assertEqual(unavailable.headers["cache-control"], "no-store")

    def test_ticket_design_pin_preserves_exact_version_and_project(self):
        from app.canvas import publish

        project = self.create("projects", name="Design criteria")["id"]
        milestone = self.create("milestones", name="Release", project=project)["id"]
        profile = self.create("documents", project=project, name="Design Profile", document_type="design-topic",
                              content="Design under review")
        self.finish_reviews(project)
        sources = [{"document_id": profile["id"], "revision": 1}]
        published = publish("Codex", profile["id"], 1, {"gallery.html": "djE="}, "Approved first design", sources)
        latest = publish("Codex", profile["id"], published["revision"], {"gallery.html": "djI="},
                         "Approved second design", [{**sources[0], "revision": published["revision"]}])
        design = dict(document_id=profile["id"], version=1)
        criterion = dict(id="read-layout", text="Current ticket uses the approved first version.", design=design)
        ticket = self.create("tickets", project=project, milestone=milestone, name="Ticket layout", criteria=[criterion])
        self.assertEqual(ticket["criteria"][0]["design"], design)
        review = self.current_review(ticket["id"])
        self.assertIn(profile["id"], [doc["id"] for doc in review["snapshot"]["documents"]])
        self.assertFalse(review["snapshot"]["missing_context"])
        unknown = self.http.post("/api/tickets", json={
            "project": project, "milestone": milestone, "name": "Invalid version",
            "criteria": [{**criterion, "design": {**design, "version": 42}}],
        })
        self.assertEqual(unknown.status_code, 422)
        other = self.create("projects", name="Other design criteria")["id"]
        other_milestone = self.create("milestones", name="Release", project=other)["id"]
        mismatch = self.http.post("/api/tickets", json={
            "project": other, "milestone": other_milestone, "name": "Invalid project", "criteria": [criterion],
        })
        self.assertEqual(mismatch.status_code, 422)
        self.approve_removal(latest)
        blocked = self.http.delete("/api/documents/" + profile["id"], params={"revision": latest["revision"]})
        self.assertEqual(blocked.status_code, 409, blocked.text)
        self.assertIn(ticket["id"], blocked.json()["detail"])

    def review_fixture(self):
        p = self.create('projects', name='Review rules')['id']
        m = self.create('milestones', name='Delivery', project=p)['id']
        d = self.create('documents', name='Scope', project=p, document_type='user-story', content='Users can save a ticket.')
        t = self.create('tickets', name='Save a ticket', description='Implement the documented Save action.',
                        project=p, milestone=m, documents=[d['id']])
        return p, m, d, t

    def test_criterion_proof_validates_pins_without_reopening_requirements(self):
        project, milestone, requirements, legacy = self.review_fixture()
        self.assertEqual(legacy["criteria"], [])
        report = self.create("documents", project=project, document_type="review-evidence", name="Save tests",
                             content="# Verification\n\n```text\n# Not a heading\n```\n\n## Failed-save result\nPassed")
        other = self.create("projects", name="Other proof project")["id"]
        external = self.create("documents", project=other, name="Unrelated", content="# Results")
        criterion = dict(id="save-failure", text="A failed save preserves user input.", evidence_required=True)
        target = dict(kind="report", document_id=report["id"], revision=report["revision"], section_line=6,
                      status="unverified")
        fields = dict(name="Verify failed saves", project=project, milestone=milestone,
                      documents=[requirements["id"]], output_documents=[report["id"]])
        for proof, outputs in (
            ({**target, "section_line": 3}, [report["id"]]),
            ({**target, "revision": 2}, [report["id"]]),
            ({**target, "document_id": external["id"], "section_line": 0}, [external["id"]]),
            (target, []),
        ):
            rejected = self.http.post("/api/tickets", json={
                **fields, "output_documents": outputs, "criteria": [{**criterion, "evidence": [proof]}],
            })
            self.assertEqual(rejected.status_code, 422, rejected.text)
        duplicate = self.http.post("/api/tickets", json={**fields, "criteria": [criterion, criterion]})
        self.assertEqual(duplicate.status_code, 422)

        ticket = self.create("tickets", **fields, criteria=[{**criterion, "evidence": [target]}])
        self.finish_reviews(project)
        review = self.current_review(ticket["id"])
        path = "/api/tickets/" + ticket["id"]
        updated = self.http.patch(path, json={"revision": 1, "changes": {
            "criteria": [{**criterion, "evidence": [{**target, "status": "verified"}]}],
        }})
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(self.current_review(ticket["id"])["id"], review["id"])
        changed_criterion = self.http.patch(path, json={"revision": 2, "changes": {
            "criteria": [{**criterion, "text": "Keep the draft on network errors.", "evidence": [target]}],
        }})
        self.assertEqual(changed_criterion.status_code, 200, changed_criterion.text)
        self.assertEqual(self.current_review(ticket["id"])["status"], "Pending")

    def test_explicit_criteria_gate_completion_and_preserve_superseded_proof(self):
        project, milestone, requirements, legacy = self.review_fixture()
        report = self.create("documents", project=project, document_type="review-evidence", name="Initial result",
                             content="## Failed save\nPassed")
        exact = dict(kind="report", document_id=report["id"], revision=1, section_line=0, status="verified")
        required = dict(id="proof-required", text="Verify the failed save.", evidence_required=True)
        ticket = self.create("tickets", name="Verify the save", project=project, milestone=milestone,
                             documents=[requirements["id"]], output_documents=[report["id"]], criteria=[required])
        self.finish_reviews(project)
        run = self.create("runs", name="Save check", project=project, agent="Codex", mode="Edit",
                          ticket=ticket["id"], status="Running")
        ticket_path, run_path = "/api/tickets/" + ticket["id"], "/api/runs/" + run["id"]

        def assert_incomplete(ticket_revision):
            for path, revision, status in ((ticket_path, ticket_revision, "Done"), (run_path, 1, "Completed")):
                result = self.http.patch(path, json={"revision": revision, "changes": {"status": status}})
                self.assertEqual(result.status_code, 409, result.text)
                self.assertIn("proof-required", result.json()["detail"])

        assert_incomplete(1)
        first = self.http.patch(ticket_path, json={"revision": 1, "changes": {
            "criteria": [{**required, "evidence": [exact]}],
        }})
        self.assertEqual(first.status_code, 200, first.text)
        changed = self.http.patch("/api/documents/" + report["id"], json={"revision": 1, "changes": {
            "content": "# Results moved\n\n## Failed save\nPassed on the new build",
        }})
        self.assertEqual(changed.status_code, 200, changed.text)
        assert_incomplete(2)  # The old revision is no longer a current proof.

        retired = {**exact, "status": "superseded"}
        next_proof = {**exact, "revision": 2, "section_line": 2}
        superseded_only = self.http.patch(ticket_path, json={"revision": 2, "changes": {
            "criteria": [{**required, "evidence": [retired]}],
        }})
        self.assertEqual(superseded_only.status_code, 200, superseded_only.text)
        assert_incomplete(3)
        resolved = self.http.patch(ticket_path, json={"revision": 3, "changes": {
            "criteria": [{**required, "evidence": [retired, next_proof]}],
        }})
        self.assertEqual(resolved.status_code, 200, resolved.text)
        self.assertEqual(resolved.json()["criteria"][0]["evidence"], [retired, next_proof])
        self.assertEqual(self.http.patch(run_path, json={"revision": 1, "changes": {"status": "Completed"}}).status_code, 200)
        self.assertEqual(self.http.patch(ticket_path, json={"revision": 4, "changes": {"status": "Done"}}).status_code, 200)
        legacy_path = "/api/tickets/" + legacy["id"]
        self.assertEqual(self.http.patch(legacy_path, json={"revision": 1, "changes": {"status": "Done"}}).status_code, 200)

    def current_review(self, key):
        return next(r for r in self.http.get('/api/workspace?view=export').json()['reviews'] if r['subject'] == key and not r['superseded'])

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
        self.assertTrue(next(r for r in self.http.get('/api/workspace?view=export').json()['reviews'] if r['id'] == review['id'])['superseded'])
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
        runs = self.http.get('/api/workspace?view=export').json()['runs']
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
                scope = {'project': p, 'subject': ticket['id'], 'limit': 1}
                latest = (await client.call_tool('list_change_reviews', scope)).data
                self.assertEqual(latest, [started])
                previous = (await client.call_tool('list_change_reviews', {**scope, 'offset': 1})).data
                self.assertEqual(len(previous), 1)
                self.assertTrue(previous[0]['superseded'])
                self.assertEqual(previous[0]['subject'], ticket['id'])
                self.assertEqual((await client.call_tool('list_change_reviews', {**scope, 'offset': 2})).data, [])
                self.assertEqual((await client.call_tool('list_change_reviews', {**scope, 'project': 'other'})).data, [])
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
        data = self.http.get('/api/workspace?view=export').json()
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
