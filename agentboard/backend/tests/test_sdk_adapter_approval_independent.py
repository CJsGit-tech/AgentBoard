"""Independent coverage for exact browser approval binding."""
import hashlib
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from app.api.errors import ApiError
from app.db.models import AgentChangeApproval
from app.sdk import routes


class ApprovalBindingTests(unittest.TestCase):
    def test_proposal_hash_binds_kind_target_revision_and_canonical_changes(self):
        project_id, target_id = uuid4(), uuid4()
        run = SimpleNamespace(project_id=project_id, id=uuid4())
        target = SimpleNamespace(id=target_id, revision=3, fields={"title": "Original ticket"})
        db = Mock()
        db.scalar.side_effect = [SimpleNamespace(id=project_id), target]
        with patch.object(routes.service, "revision"):
            approval = routes.create_change_proposal(db, run, routes.ChangeProposal(
                operation="update", target_kind="ticket", target_id=target_id, expected_revision=3,
                changes={"status": "in_progress", "title": "A"}))
        canonical = json.dumps({"operation": "update", "kind": "ticket", "id": str(target_id), "revision": 3,
                                "changes": {"status": "in_progress", "title": "A"}},
                               sort_keys=True, separators=(",", ":"))
        self.assertEqual(approval.change_hash, hashlib.sha256(canonical.encode()).hexdigest())
        self.assertEqual(approval.status, "pending")
        self.assertEqual(approval.proposed_changes["title"], "A")
        self.assertTrue(any(isinstance(call.args[0], AgentChangeApproval) for call in db.add.call_args_list))

    def test_decision_rejects_hash_and_revision_mismatch_without_mutating(self):
        project_id, target_id = uuid4(), uuid4()
        approval = SimpleNamespace(id=uuid4(), project_id=project_id, status="pending", decision_key=None,
            change_hash="a" * 64, base_revision=2, target_kind="ticket", target_id=target_id,
            proposed_changes={"title": "safe"})
        db = Mock()
        db.scalar.side_effect = [SimpleNamespace(id=project_id), approval]
        for payload in (
            routes.ApprovalDecision(decision="approve", change_hash="b" * 64, expected_revision=2),
            routes.ApprovalDecision(decision="approve", change_hash="a" * 64, expected_revision=1),
        ):
            db.scalar.side_effect = [SimpleNamespace(id=project_id), approval]
            with self.assertRaises(ApiError) as raised:
                routes.decide_approval(project_id, approval.id, payload, key="decision-key", db=db)
            self.assertEqual(raised.exception.code, "approval_mismatch")
            self.assertEqual(approval.status, "pending")
            db.commit.assert_not_called()

    def test_approval_returns_stale_revision_before_applying(self):
        project_id, target_id = uuid4(), uuid4()
        approval = SimpleNamespace(id=uuid4(), project_id=project_id, status="pending", decision_key=None,
            change_hash="a" * 64, base_revision=2, target_kind="ticket", target_id=target_id,
            proposed_changes={"title": "safe"})
        row = SimpleNamespace(revision=3)
        db = Mock()
        db.scalar.side_effect = [SimpleNamespace(id=project_id), approval, None, row]
        body = routes.ApprovalDecision(decision="approve", change_hash="a" * 64, expected_revision=2)
        with patch.object(routes.service, "revision", side_effect=ApiError(409, "stale_revision", "stale")):
            with self.assertRaises(ApiError) as raised:
                routes.decide_approval(project_id, approval.id, body, key="decision-key", db=db)
        self.assertEqual(raised.exception.code, "stale_revision")
        db.commit.assert_called_once()
        self.assertEqual(approval.status, "stale")
        self.assertEqual(approval.decision_key, "decision-key")
        self.assertIsNotNone(approval.decision_hash)
        self.assertEqual(approval.decided_by, "browser")

    def test_approval_success_applies_exact_bound_changes_and_audits(self):
        project_id, target_id = uuid4(), uuid4()
        approval = SimpleNamespace(id=uuid4(), project_id=project_id, status="pending", decision_key=None,
            change_hash="a" * 64, base_revision=2, target_kind="ticket", target_id=target_id,
            proposed_changes={"title": "approved"}, decision_hash=None, operation="update")
        row = SimpleNamespace(revision=2)
        db = Mock()
        db.scalar.side_effect = [SimpleNamespace(id=project_id), approval, None, row]
        body = routes.ApprovalDecision(decision="approve", change_hash="a" * 64, expected_revision=2)
        with patch.object(routes.service, "revision"), patch.object(routes, "validate") as validate, \
                patch.object(routes.service, "update") as update:
            result = routes.decide_approval(project_id, approval.id, body, key="approval-key", db=db)
        self.assertEqual(result["status"], "approved")
        validate.assert_called_once_with("TicketUpdate", {"expected_revision": 2,
                                                           "changes": {"title": "approved"}})
        update.assert_called_once_with(db, row, {"title": "approved"}, commit=False)
        self.assertEqual(approval.decision_key, "approval-key")
        self.assertEqual(approval.decision_hash, hashlib.sha256(json.dumps(
            body.model_dump(), sort_keys=True, separators=(",", ":")).encode()).hexdigest())
        db.commit.assert_called_once()

    def test_same_key_retry_returns_existing_status_but_cross_approval_key_is_rejected(self):
        project_id = uuid4()
        retry_body = routes.ApprovalDecision(decision="approve", change_hash="a" * 64, expected_revision=1)
        retry_digest = hashlib.sha256(json.dumps(retry_body.model_dump(), sort_keys=True,
                                                 separators=(",", ":")).encode()).hexdigest()
        approval = SimpleNamespace(id=uuid4(), project_id=project_id, status="approved", decision_key="k",
                                   decision_hash=retry_digest)
        db = Mock()
        db.scalar.side_effect = [SimpleNamespace(id=project_id), approval]
        result = routes.decide_approval(project_id, approval.id,
            retry_body, key="k", db=db)
        self.assertEqual(result["status"], "approved")
        db.commit.assert_not_called()

        db.scalar.side_effect = [SimpleNamespace(id=project_id), approval]
        with self.assertRaises(ApiError) as raised:
            routes.decide_approval(project_id, approval.id,
                routes.ApprovalDecision(decision="reject", change_hash="a" * 64, expected_revision=1),
                key="k", db=db)
        self.assertEqual(raised.exception.code, "idempotency_key_reused")

        pending = SimpleNamespace(id=uuid4(), project_id=project_id, status="pending", decision_key=None,
            change_hash="a" * 64, base_revision=1, target_kind="ticket", target_id=uuid4(),
            proposed_changes={"title": "x"})
        other = SimpleNamespace(id=uuid4())
        db.scalar.side_effect = [SimpleNamespace(id=project_id), pending, other]
        with self.assertRaises(ApiError) as raised:
            routes.decide_approval(project_id, pending.id,
                routes.ApprovalDecision(decision="approve", change_hash="a" * 64, expected_revision=1),
                key="already-used", db=db)
        self.assertEqual(raised.exception.code, "idempotency_key_reused")

    def test_cross_project_approval_is_not_found_after_parent_lock(self):
        project_id = uuid4()
        db = Mock()
        db.scalar.side_effect = [SimpleNamespace(id=project_id), None]
        body = routes.ApprovalDecision(decision="reject", change_hash="a" * 64, expected_revision=1)
        with self.assertRaises(ApiError) as raised:
            routes.decide_approval(project_id, uuid4(), body, key="key", db=db)
        self.assertEqual(raised.exception.status, 404)
        self.assertEqual(db.scalar.call_count, 2)
        db.commit.assert_not_called()

    def test_decline_records_rejection_without_applying_changes(self):
        project_id = uuid4()
        approval = SimpleNamespace(id=uuid4(), project_id=project_id, status="pending", decision_key=None,
            change_hash="a" * 64, base_revision=2, target_kind="ticket", target_id=uuid4(),
            proposed_changes={"title": "safe"}, decision_hash=None)
        db = Mock()
        db.scalar.side_effect = [SimpleNamespace(id=project_id), approval, None]
        body = routes.ApprovalDecision(decision="reject", change_hash="a" * 64, expected_revision=2)
        with patch.object(routes.service, "update") as update:
            result = routes.decide_approval(project_id, approval.id, body, key="decline-key", db=db)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(approval.decision_key, "decline-key")
        self.assertIsNotNone(approval.decision_hash)
        update.assert_not_called()
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
