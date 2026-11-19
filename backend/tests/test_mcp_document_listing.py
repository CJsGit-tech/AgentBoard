from unittest import TestCase
from uuid import uuid4

from app.mcp.catalog import TOOLS


class DocumentListingContractTests(TestCase):
    def test_bundled_schema_accepts_full_records_summaries_and_empty_pages(self):
        validate = TOOLS["list_documents"]["output_validator"].validate
        summary = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "revision": 1,
            "created_at": "2026-11-19T12:00:00Z",
            "updated_at": "2026-11-19T12:00:00Z",
            "title": "Example document",
            "description": "A short summary.",
            "kind": "document",
            "tags": [],
            "version": 1,
            "current_version_id": str(uuid4()),
            "source": "manual",
            "source_id": None,
        }
        for items in ([], [summary], [{**summary, "content": "Body text"}]):
            with self.subTest(items=items):
                validate({"outcome": "success", "applied": False,
                          "data": {"items": items, "next_cursor": None}})
