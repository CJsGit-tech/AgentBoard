from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch
from uuid import uuid4

from mcp.types import ElicitResult, InputRequiredResult

from app.mcp import operations
from app.mcp.auth import McpClient


class ApprovalFlowTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_id = uuid4()
        self.request = SimpleNamespace(
            id=uuid4(),
            project_id=self.project_id,
            ticket_id=None,
            status="pending",
            operation="update",
            proposed_changes={"purpose": "Proposed update"},
            base_revision=1,
        )
        self.database = Mock()
        self.context = SimpleNamespace(protocol_version="2026-07-28")

    async def request_update(self, client):
        return await operations._approval_flow(
            self.context,
            self.database,
            client,
            project_id=self.project_id,
            target_kind="project",
            target_id=self.project_id,
            operation="update",
            changes=self.request.proposed_changes,
            expected_revision=1,
            operation_key="test-approval",
        )

    async def test_unverified_client_leaves_the_request_pending(self):
        client = McpClient(uuid4(), "Unverified client")
        with (
            patch.object(operations, "create_mutation_request", return_value=self.request),
            patch.object(operations, "_ask_client") as ask_client,
            patch.object(operations, "_apply_mutation") as apply_mutation,
        ):
            result = await self.request_update(client)

        self.assertEqual(operations._mutation_outcome(result)["outcome"], "approval_required")
        self.assertEqual(self.request.status, "pending")
        ask_client.assert_not_called()
        apply_mutation.assert_not_called()

    async def test_input_required_conditions_return_the_form_without_applying(self):
        client = McpClient(uuid4(), "Verified test client", interactive_approval_verified=True)
        with (
            patch.object(operations, "create_mutation_request", return_value=self.request),
            patch.object(operations, "_target_label", return_value="Test project"),
            patch.object(operations, "_apply_mutation") as apply_mutation,
        ):
            result = await self.request_update(client)

        self.assertIsInstance(result, InputRequiredResult)
        self.assertIn("approval", result.input_requests)
        self.assertEqual(result.request_state, str(self.request.id))
        self.assertEqual(self.request.status, "pending")
        apply_mutation.assert_not_called()

    async def test_a_form_answer_without_matching_request_state_is_insufficient(self):
        response = ElicitResult(action="accept", content={"approved": True})
        for request_state in (None, str(uuid4())):
            with self.subTest(request_state=request_state):
                token = operations.input_round.set((request_state, {"approval": response}))
                try:
                    result = await operations._ask_client(self.context, self.request.id, "Approve?", {})
                finally:
                    operations.input_round.reset(token)
                self.assertIsNone(result)
