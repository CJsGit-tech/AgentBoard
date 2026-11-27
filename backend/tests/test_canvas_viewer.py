"""The reader loads a publication and the evidence necessary for its delivery links."""
import unittest
from uuid import uuid4

from app.db import connect
from tests import test_contracts as fixtures


class CanvasViewerIntegration(unittest.TestCase):
    setUp = fixtures.WorkspaceIntegration.setUp
    create = fixtures.WorkspaceIntegration.create

    def test_standalone_publication_metadata_and_proof_targets(self):
        project = self.create("projects", name="Reader")["id"]
        milestone = self.create("milestones", name="Milestone", project=project)["id"]
        profile = self.create("documents", name="Design", document_type="design-canvas",
                              project=project, content="Private design narrative")["id"]
        report = self.create("documents", name="Evidence", document_type="review-evidence",
                             project=project, content="Private report body\n## Verified\n```\n## Example\n```")
        self.create("documents", name="Unrelated", project=project, content="Other payload")
        path = f"/api/canvases/{profile}/viewer"
        self.assertEqual(self.http.get(path).status_code, 404)
        with connect() as conn:
            for version in (1, 2):
                conn.execute("INSERT INTO canvas_versions(document_id,version,asset_key,digest) VALUES (%s,%s,%s,%s)",
                             (profile, version, uuid4(), str(version) * 64))
        capture = self.create("documents", project=project, name="Screens", content="Long screenshot inventory",
                              document_type="screen-inventory")
        digest = "d" * 64
        with connect() as conn:
            conn.execute("INSERT INTO visual_assets(document_id,filename,digest,image) VALUES (%s,'saved.png',%s,%s)",
                         (capture["id"], digest, b'original'))
        proof = {"document_id": report["id"], "kind": "report", "revision": report["revision"],
                 "section_line": 1, "status": "verified"}
        screen = {"document_id": capture["id"], "kind": "screenshot", "filename": "saved.png",
                  "digest": digest, "status": "verified"}
        pinned = self.create("tickets", name="Pinned", milestone=milestone, project=project,
                             output_documents=[report["id"], capture["id"]], description="Lengthy implementation plan",
                             criteria=[{"id": "show", "text": "Render preview", "evidence_required": True,
                                        "design": {"document_id": profile, "version": 2}, "evidence": [proof, screen]}])
        legacy = self.create("tickets", name="Legacy", milestone=milestone, project=project,
                             documents=[profile], description=f"Historical prose [Preview](#canvas/{profile}/1)")
        self.create("tickets", name="Unrelated ticket", milestone=milestone, project=project)
        response = self.http.get(path)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual([r["id"] for r in data["projects"]], [project])
        self.assertEqual([r["id"] for r in data["tickets"]], [pinned["id"], legacy["id"]])
        self.assertEqual(data["tickets"][0]["criteria"], [{"design": {"document_id": profile, "version": 2},
                                                           "evidence": [proof, screen]}])
        self.assertEqual(data["tickets"][1]["description"], f"[Preview](#canvas/{profile}/1)")
        self.assertEqual([v["version"] for v in data["documents"][0]["canvas_versions"]], [2, 1])
        documents = {doc["id"]: doc for doc in data["documents"]}
        self.assertEqual(documents[report["id"]]["report_heading_lines"], [1])
        self.assertEqual(documents[capture["id"]]["previews"], [{"filename": "saved.png", "digest": digest}])
        for excluded in ("Private design narrative", "Private report body", "Other payload", "Unrelated ticket",
                         "Render preview", "Historical prose", "Lengthy implementation plan"):
            self.assertNotIn(excluded, response.text)
        self.assertEqual(self.http.get(path, headers={"X-AgentBoard-UI": ""}).status_code, 403)
        with connect() as conn:
            conn.execute("UPDATE records SET deleted=true WHERE id=%s", (report["id"],))
        self.assertEqual({d["id"] for d in self.http.get(path).json()["documents"]}, {profile, capture["id"]})
        with connect() as conn:
            conn.execute("UPDATE records SET deleted=true WHERE id=%s", (profile,))
        self.assertEqual(self.http.get(path).status_code, 404)
