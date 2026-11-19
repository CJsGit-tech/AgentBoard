"""Independent, provider-free coverage for SDK run adapters and approvals."""
import hashlib
import json
import sys
import os
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from app.api.errors import ApiError
from app.db.models import AgentChangeApproval
from app.sdk import adapters, routes


class AdapterContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_codex_adapter_passes_prompt_and_returns_response_text(self):
        calls, configs, starts, logins = [], [], [], []

        class FakeConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                configs.append(kwargs)

        class FakeCodex:
            def __init__(self, *, config):
                self.config = config

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            async def login_api_key(self, api_key):
                logins.append((api_key, self.config.kwargs["env"]["CODEX_HOME"]))

            async def thread_start(self, **kwargs):
                starts.append(kwargs)
                return SimpleNamespace(run=response_run)

        async def response_run(prompt, **kwargs):
            calls.append((prompt, kwargs))
            return SimpleNamespace(final_response="codex answer")

        fake = types.ModuleType("openai_codex")
        fake.ApprovalMode = SimpleNamespace(deny_all="deny_all")
        fake.AsyncCodex = FakeCodex
        fake.CodexConfig = FakeConfig
        fake.Sandbox = SimpleNamespace(read_only="read_only")
        activity = Mock()
        with patch.dict(sys.modules, {"openai_codex": fake}), patch.dict("os.environ", {
                "OPENAI_API_KEY": "test-openai-key", "ANTHROPIC_API_KEY": "other-test-key",
                "DATABASE_URL": "test-db", "AGENTBOARD_BROWSER_TOKEN_FILE": "test-browser-token"}):
            result = await adapters.CodexSDKAdapter().run("do work", activity=activity)
        self.assertEqual(result, {"text": "codex answer"})
        self.assertEqual(calls[0][0], "do work")
        self.assertTrue(starts[0]["ephemeral"])
        self.assertEqual(starts[0]["sandbox"], "read_only")
        self.assertEqual(starts[0]["approval_mode"], "deny_all")
        self.assertEqual(starts[0]["cwd"], "/tmp")
        self.assertEqual(configs[0]["cwd"], "/tmp")
        self.assertIn("features.shell_tool=false", configs[0]["config_overrides"])
        self.assertIn("features.unified_exec=false", configs[0]["config_overrides"])
        self.assertIn("mcp_servers={}", configs[0]["config_overrides"])
        self.assertEqual(configs[0]["env"]["OPENAI_API_KEY"], "test-openai-key")
        self.assertEqual(logins[0][0], "test-openai-key")
        self.assertFalse(os.path.exists(logins[0][1]))
        self.assertEqual(configs[0]["env"]["CODEX_HOME"], logins[0][1])
        for key in ("ANTHROPIC_API_KEY", "DATABASE_URL", "AGENTBOARD_BROWSER_TOKEN_FILE", "AGENTBOARD_MCP_TOKEN_FILE"):
            self.assertEqual(configs[0]["env"][key], "")
        self.assertEqual(activity.call_args.args, ("provider_message", "codex answer"))

    async def test_claude_adapter_collects_messages_and_emits_ordered_activity(self):
        seen, calls = [], []

        class FakeOptions:
            def __init__(self, **kwargs):
                seen.append(kwargs)

        class FakeTextBlock:
            def __init__(self, text):
                self.text = text

        class FakeAssistantMessage:
            def __init__(self, content):
                self.content = content

        class FakeResultMessage:
            def __init__(self, result):
                self.result = result

        async def query(*, prompt, options):
            calls.append((prompt, options))
            for item in ("first", "second"):
                yield FakeAssistantMessage([FakeTextBlock(item)])
            yield FakeResultMessage("final")

        fake = types.ModuleType("claude_agent_sdk")
        fake.AssistantMessage = FakeAssistantMessage
        fake.ClaudeAgentOptions = FakeOptions
        fake.ResultMessage = FakeResultMessage
        fake.TextBlock = FakeTextBlock
        fake.query = query
        activity = Mock()
        with patch.dict(sys.modules, {"claude_agent_sdk": fake}), patch.dict("os.environ", {
                "ANTHROPIC_API_KEY": "test-anthropic-key", "OPENAI_API_KEY": "other-test-key",
                "DATABASE_URL": "test-db", "AGENTBOARD_MCP_TOKEN_FILE": "test-mcp-token"}):
            result = await adapters.ClaudeAgentSDKAdapter().run("do work", activity=activity)
        self.assertEqual(result, {"text": "firstsecond"})
        self.assertEqual(calls[0][0], "do work")
        self.assertEqual(seen[0]["env"]["ANTHROPIC_API_KEY"], "test-anthropic-key")
        for key in ("OPENAI_API_KEY", "DATABASE_URL", "AGENTBOARD_BROWSER_TOKEN_FILE", "AGENTBOARD_MCP_TOKEN_FILE"):
            self.assertEqual(seen[0]["env"][key], "")
        self.assertEqual(seen[0]["tools"], [])
        self.assertEqual(seen[0]["allowed_tools"], [])
        self.assertEqual(seen[0]["mcp_servers"], {})
        self.assertEqual(seen[0]["setting_sources"], [])
        self.assertEqual(seen[0]["plugins"], [])
        self.assertEqual(seen[0]["skills"], [])
        self.assertEqual(seen[0]["permission_mode"], "dontAsk")
        self.assertEqual(seen[0]["max_turns"], 1)
        self.assertEqual(seen[0]["cwd"], "/tmp")
        self.assertEqual([call.args for call in activity.call_args_list], [
            ("provider_message", "first"), ("provider_message", "second")])

    async def test_missing_sdk_package_fails_closed_without_credentials(self):
        with patch.dict(sys.modules, {"openai_codex": None, "claude_agent_sdk": None}):
            with self.assertRaisesRegex(RuntimeError, "openai-codex package is not installed"):
                await adapters.CodexSDKAdapter().run("x", activity=Mock())
            with self.assertRaisesRegex(RuntimeError, "claude-agent-sdk package is not installed"):
                await adapters.ClaudeAgentSDKAdapter().run("x", activity=Mock())

    def test_provider_readiness_checks_official_packages_flags_and_credentials(self):
        settings = SimpleNamespace(codex_sdk_enabled=True, claude_agent_sdk_enabled=True,
                                   openai_api_key=" \t", anthropic_api_key="test-anthropic-key")
        with patch.object(routes, "settings", settings), \
                patch.object(routes.importlib.util, "find_spec", side_effect=lambda name: object() if name == "claude_agent_sdk" else None) as find_spec:
            providers = routes._provider_readiness()
        self.assertEqual([call.args[0] for call in find_spec.call_args_list], ["openai_codex", "claude_agent_sdk"])
        self.assertFalse(providers["codex"]["available"])
        self.assertIn("package is not installed", providers["codex"]["reason"])
        self.assertTrue(providers["claude"]["available"])

        settings.openai_api_key = "test-openai-key"
        with patch.object(routes, "settings", settings), patch.object(routes.importlib.util, "find_spec", return_value=object()):
            providers = routes._provider_readiness()
        self.assertTrue(providers["codex"]["available"])

        settings.codex_sdk_enabled = False
        settings.anthropic_api_key = " \t"
        with patch.object(routes, "settings", settings), patch.object(routes.importlib.util, "find_spec", return_value=object()):
            providers = routes._provider_readiness()
        self.assertFalse(providers["codex"]["available"])
        self.assertEqual(providers["codex"]["reason"], "Disabled by server configuration")
        self.assertFalse(providers["claude"]["available"])
        self.assertEqual(providers["claude"]["reason"], "Claude Agent API credential is not configured")

    async def test_run_executor_records_disabled_or_adapter_failure(self):
        for provider, enabled_name, expected in (
            ("codex", "codex_sdk_enabled", "Disabled by server configuration"),
            ("claude", "claude_agent_sdk_enabled", "Disabled by server configuration"),
        ):
            run = SimpleNamespace(id=uuid4(), status="queued", provider=provider, prompt="p",
                                  activity=[], result=None, error=None)
            db = Mock()
            db.get.return_value = run
            settings = SimpleNamespace(sdk_runs_enabled=True, codex_sdk_enabled=False,
                                       claude_agent_sdk_enabled=False, openai_api_key=None, anthropic_api_key=None)
            with self.subTest(provider=provider), patch.object(routes, "SessionLocal", return_value=db), \
                    patch.object(routes, "settings", settings), patch.object(routes, "adapter_for") as adapter, \
                    patch.object(routes, "_provider_readiness", return_value={provider: {"available": False, "reason": "Disabled by server configuration"}}):
                await routes.execute_run(run.id)
            adapter.assert_not_called()
            self.assertEqual(run.status, "failed")
            self.assertIn(expected, run.error)
            self.assertEqual(run.activity[-1]["type"], "run_failed")
            db.close.assert_called_once()

        run = SimpleNamespace(id=uuid4(), status="queued", provider="codex", prompt="p",
                              selected_context=None, activity=[], result=None, error=None)
        db = Mock()
        db.get.return_value = run
        fake_adapter = Mock()
        fake_adapter.run = unittest.mock.AsyncMock(side_effect=RuntimeError("provider unavailable"))
        settings = SimpleNamespace(codex_sdk_enabled=True, claude_agent_sdk_enabled=False,
                                   openai_api_key="test-openai-key", anthropic_api_key=None)
        with patch.object(routes, "SessionLocal", return_value=db), patch.object(routes, "settings", settings), \
                patch.object(routes, "adapter_for", return_value=fake_adapter), \
                patch.object(routes, "_provider_readiness", return_value={"codex": {"available": True, "reason": None}}):
            await routes.execute_run(run.id)
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.error, "provider unavailable")


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
