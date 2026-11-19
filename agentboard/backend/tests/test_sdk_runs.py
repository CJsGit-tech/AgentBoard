import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.sdk import routes
from app.sdk.routes import ChangeProposal


class SDKRunTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_is_mocked_and_run_lifecycle_is_persisted(self):
        run = SimpleNamespace(id=uuid4(), provider="codex", status="queued", prompt="hello",
                              selected_context=None, activity=[], result=None, error=None)
        db = Mock()
        db.get.return_value = run
        adapter = Mock()
        adapter.run = AsyncMock(return_value={"text": "mocked"})
        ready = {"available": True, "reason": None}
        with patch.object(routes, "SessionLocal", return_value=db), \
             patch.object(routes, "adapter_for", return_value=adapter), \
             patch.object(routes, "_provider_readiness", return_value={"codex": ready, "claude": ready}):
            await routes.execute_run(run.id)
        self.assertEqual(run.status, "completed")
        self.assertEqual(run.result, "mocked")
        self.assertEqual(run.activity[-1]["type"], "run_completed")
        adapter.run.assert_awaited_once()
        db.close.assert_called_once()

    async def test_unconfigured_provider_fails_closed_without_sdk_call(self):
        run = SimpleNamespace(id=uuid4(), provider="claude", status="queued", prompt="hello",
                              selected_context=None, activity=[], result=None, error=None)
        db = Mock()
        db.get.return_value = run
        unavailable = {"available": False, "reason": "Disabled by server configuration"}
        with patch.object(routes, "SessionLocal", return_value=db), \
             patch.object(routes, "_provider_readiness", return_value={"codex": unavailable, "claude": unavailable}), \
             patch.object(routes, "adapter_for") as adapter_for:
            await routes.execute_run(run.id)
        self.assertEqual(run.status, "failed")
        self.assertIn("Disabled by server configuration", run.error)
        adapter_for.assert_not_called()

    def test_selected_context_has_provider_target_id_and_retry_skips_missing_record(self):
        project_id, record_id = uuid4(), uuid4()
        body = routes.RunCreate(provider="codex", prompt="Review this", context_kind="ticket", context_id=record_id)
        record = SimpleNamespace(id=record_id, revision=3, fields={"title": "Selected"})
        created_runs = []

        class FakeRun:
            def __init__(self, **values):
                self.__dict__.update(values)
                self.id = uuid4()
                self.created_at = self.updated_at = __import__("datetime").datetime.now()
                self.result = None
                self.error = None
                created_runs.append(self)

        db = Mock()
        db.get.side_effect = [SimpleNamespace(sdk_runs_enabled=True), SimpleNamespace(id=project_id)]
        db.scalar.return_value = record
        with patch.object(routes, "AgentRun", FakeRun), \
             patch.object(routes, "reserve", return_value=(SimpleNamespace(result_json=None), True)) as reserve, \
             patch.object(routes, "_provider_readiness", return_value={"codex": {"available": True, "reason": None}}):
            submitted = routes.start_run(project_id, body, Mock(), key="new-key", db=db)
        self.assertEqual(created_runs[0].selected_context["record"]["id"], str(record_id))
        self.assertEqual(created_runs[0].selected_context["record"]["revision"], 3)
        self.assertNotIn(str(record_id), submitted.values())
        self.assertEqual(reserve.call_args.args[3]["context_id"], str(record_id))
        self.assertEqual(reserve.call_args.args[3]["provider"], "codex")

        previous = {"id": str(uuid4()), "project_id": str(project_id), "provider": "codex", "status": "queued",
                    "activity": [], "result": None, "error": None, "created_at": "now", "updated_at": "now"}
        operation = SimpleNamespace(result_json=previous)
        db = Mock()
        db.get.side_effect = [SimpleNamespace(sdk_runs_enabled=True), SimpleNamespace(id=project_id)]
        with patch.object(routes, "reserve", return_value=(operation, False)) as reserve, \
             patch.object(routes, "_provider_readiness", side_effect=AssertionError("retry must not recheck provider")):
            result = routes.start_run(project_id, body, Mock(), key="retry-key", db=db)
        self.assertEqual(result, previous)
        self.assertEqual(reserve.call_args.args[3]["context_id"], str(record_id))

    def test_proposal_hash_binds_kind_id_revision_and_change(self):
        db = Mock()
        run = SimpleNamespace(id=uuid4(), project_id=uuid4())
        target = SimpleNamespace(id=uuid4(), revision=7, fields={"title": "Record"})
        db.scalar.side_effect = [SimpleNamespace(id=run.project_id), target,
                                 SimpleNamespace(id=run.project_id), target]
        with patch.object(routes.service, "revision"):
            first = routes.create_change_proposal(db, run, ChangeProposal(
                operation="update", target_kind="ticket", target_id=target.id, expected_revision=7,
                changes={"title": "approved value"}))
            second = routes.create_change_proposal(db, run, ChangeProposal(
                operation="update", target_kind="ticket", target_id=target.id, expected_revision=7,
                changes={"title": "different value"}))
        self.assertNotEqual(first.change_hash, second.change_hash)
        self.assertEqual(first.base_revision, 7)
        self.assertEqual(first.status, "pending")

    def test_marked_provider_envelope_creates_one_pending_proposal(self):
        run = SimpleNamespace(id=uuid4(), project_id=uuid4())
        db = Mock()
        approval = SimpleNamespace(id=uuid4(), target_label="Selected record", base_revision=4)
        for kind in ("ticket", "document"):
            for operation in ("update", "delete"):
                with self.subTest(kind=kind, operation=operation):
                    payload = {"type": "proposal", "operation": operation, "target_kind": kind,
                               "target_id": str(uuid4()), "expected_revision": 4,
                               "changes": {"title": "updated"} if operation == "update" else {}}
                    with patch.object(routes, "create_change_proposal", return_value=approval) as create:
                        result = routes._parse_provider_response(db, run, {"text": __import__("json").dumps({"agentboard": payload})})
                    self.assertIn(f"{operation} {kind}", result)
                    create.assert_called_once()
                    self.assertEqual(create.call_args.args[2].operation, operation)

    def test_real_proposal_envelope_validates_marker_and_hides_approval_identifier(self):
        run = SimpleNamespace(id=uuid4(), project_id=uuid4())
        approval = SimpleNamespace(id=uuid4(), target_label="Readable task", base_revision=2)
        payload = {"type": "proposal", "operation": "update", "target_kind": "ticket",
                   "target_id": str(uuid4()), "expected_revision": 2, "changes": {"title": "Updated"}}
        with patch.object(routes, "create_change_proposal", return_value=approval) as create:
            result = routes._parse_provider_response(None, run, {"text": __import__("json").dumps({"agentboard": payload})})
        self.assertIn("update ticket 'Readable task'", result)
        self.assertNotIn(str(approval.id), result)
        create.assert_called_once()
        self.assertEqual(create.call_args.args[2].target_id, __import__("uuid").UUID(payload["target_id"]))

    def test_ordinary_provider_text_is_preserved_and_unsupported_kind_rejected(self):
        self.assertEqual(routes._parse_provider_response(Mock(), Mock(), {"text": "hello"}), "hello")
        payload = {"agentboard": {"type": "proposal", "operation": "update", "target_kind": "project",
                                  "target_id": str(uuid4()), "expected_revision": 1, "changes": {"name": "x"}}}
        with self.assertRaises(Exception) as raised:
            routes._parse_provider_response(Mock(), Mock(), {"text": __import__("json").dumps(payload)})
        self.assertEqual(getattr(raised.exception, "code", None), "unsupported_proposal_kind")


if __name__ == "__main__":
    unittest.main()
