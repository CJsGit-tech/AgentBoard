"""Assistant transaction and checkout-queue race tests; no provider calls."""
import asyncio
import json
import os
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from agents import RunContextWrapper

from tests import test_contracts as fixtures
from app import assistant, assistant_store as store
from app.assistant_provider import CredentialStore
from app.assistant_workspace import WorkspaceHandle
from app.db import connect
from app.store import Problem, get_row


class AssistantRaceTests(unittest.TestCase):
    create = fixtures.WorkspaceIntegration.create
    finish_reviews = fixtures.WorkspaceIntegration.finish_reviews

    def setUp(self):
        self.enterContext(patch.dict(os.environ, AGENTBOARD_ASSISTANT_WORKER="0"))
        fixtures.WorkspaceIntegration.setUp(self)
        self.enterContext(
            patch.object(
                assistant,
                "credentials",
                CredentialStore(environment_key="test-not-a-real-provider-key"),
            )
        )
        self.project = self.create("projects", name="Assistant race fixture")
        self.chat = self.new_chat()

    def new_chat(self):
        response = self.http.post(
            "/api/assistant/projects/" + self.project["id"] + "/conversations", json={}
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def approved_ticket(self, **fields):
        milestone = self.create(
            "milestones", name="First milestone", project=self.project["id"]
        )
        document = self.create(
            "documents",
            name="Assistant requirements",
            project=self.project["id"],
            content="The ticket stays within this fixture's scope.",
        )
        ticket = self.create(
            "tickets",
            name="Reviewed assistant task",
            project=self.project["id"],
            milestone=milestone["id"],
            documents=[document["id"]],
            **fields,
        )
        self.finish_reviews(self.project["id"])
        return ticket

    def create_run(self, conversation_id, *, mode="Read only", ticket_id=""):
        payload = {
            "request_id": str(uuid4()),
            "message": "Complete the reviewed task.",
            "model": assistant.config()["models"][0]["id"],
            "mode": mode,
        }
        if ticket_id:
            payload["ticket_id"] = ticket_id
        response = self.http.post(
            "/api/assistant/conversations/" + conversation_id + "/runs", json=payload
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_cancel_winning_atomic_finish_does_not_mark_ticket_done(self):
        ticket = self.approved_ticket()
        handle = WorkspaceHandle(
            Path("/workspaces/race-project"), "/host/race-project", "fixture-config"
        )
        with patch.object(assistant.workspace, "require_workspace", return_value=handle), patch.object(
            assistant.workspace,
            "execution_status",
            return_value={"config_id": "fixture-config"},
        ):
            run = self.create_run(self.chat["id"], mode="Edit", ticket_id=ticket["id"])

        claimed = store.claim("race-test-worker")
        self.assertEqual(str(claimed["id"]), run["id"])
        store.update(run["id"], step="Verified commit created")

        # Model the finalization window after the filesystem commit but before
        # the atomic database transaction records both Ticket Done and run end.
        store.cancel(run["id"])
        final = store.finish(
            run["id"],
            "The run was stopped before finalization.",
            [{"role": "assistant", "content": "The run was stopped before finalization."}],
            ticket_done=True,
        )

        with connect() as conn:
            saved_ticket = get_row(conn, "tickets", ticket["id"])
        self.assertEqual(final["status"], "Cancelled")
        self.assertTrue(final["cancelled"])
        self.assertEqual(saved_ticket["data"]["status"], "Planned")
        self.assertEqual(store.events(run["id"], 0)["events"][-1]["type"], "run.cancelled")

    def test_managed_finish_rechecks_explicit_criterion_proof_before_completion(self):
        criterion = dict(id="verified-load", text="Confirm that saved data loads.", evidence_required=True)
        result = self.create("documents", name="Load result", project=self.project["id"],
                             document_type="review-evidence", content="## Load check\nPassed.")
        ticket = self.approved_ticket(criteria=[criterion], output_documents=[result["id"]])
        handle = WorkspaceHandle(
            Path("/workspaces/race-project"), "/host/race-project", "fixture-config"
        )
        with patch.object(assistant.workspace, "require_workspace", return_value=handle), patch.object(
            assistant.workspace, "execution_status", return_value={"config_id": "fixture-config"}
        ):
            run = self.create_run(self.chat["id"], mode="Edit", ticket_id=ticket["id"])
        self.assertEqual(str(store.claim("race-test-worker")["id"]), run["id"])
        with self.assertRaisesRegex(Problem, "verified-load"):
            store.require_completion_evidence(run["id"])
        with self.assertRaisesRegex(Problem, "verified-load"):
            store.finish(run["id"], "The result still needs an exact proof.", [])
        self.assertEqual(store.get_run(run["id"])["status"], "Running")

        proof = dict(kind="report", document_id=result["id"], revision=result["revision"],
                     section_line=0, status="verified")
        attached = self.http.patch("/api/tickets/" + ticket["id"], json={"revision": ticket["revision"],
                                   "changes": {"criteria": [{**criterion, "evidence": [proof]}]}})
        self.assertEqual(attached.status_code, 200, attached.text)
        store.require_completion_evidence(run["id"])
        final = store.finish(run["id"], "The matching test result is recorded.", [], ticket_done=True)
        self.assertEqual(final["status"], "Completed")
        with connect() as conn:
            self.assertEqual(get_row(conn, "tickets", ticket["id"])["data"]["status"], "Done")

    def test_cancelled_uncertain_edit_keeps_same_folder_queue_locked(self):
        ticket = self.approved_ticket()
        handle = WorkspaceHandle(
            Path("/workspaces/shared-project"), "/host/shared-project", "fixture-config"
        )
        with patch.object(assistant.workspace, "require_workspace", return_value=handle), patch.object(
            assistant.workspace,
            "execution_status",
            return_value={"config_id": "fixture-config"},
        ):
            first = self.create_run(self.chat["id"], mode="Edit", ticket_id=ticket["id"])
            second_chat = self.new_chat()
            second = self.create_run(second_chat["id"], mode="Edit", ticket_id=ticket["id"])

        claimed = store.claim("race-test-worker")
        self.assertEqual(str(claimed["id"]), first["id"])

        # Preserve an unresolved tool attempt on a terminal row. This covers
        # recovery from older cancellation paths as well as current Waiting runs.
        with connect() as conn:
            conn.execute(
                "UPDATE assistant_runs SET status='Cancelled',cancelled=true,restore_point=NULL WHERE id=%s",
                (first["id"],),
            )
            attempt_id = uuid4()
            conn.execute(
                """INSERT INTO assistant_tool_attempts(id,run_id,name,input_digest,state)
                   VALUES(%s,%s,'write_file','fixture','started')""",
                (attempt_id, first["id"]),
            )

        self.assertIsNone(store.claim("second-worker"))
        self.assertEqual(store.get_run(second["id"])["status"], "Queued")

        with connect() as conn:
            conn.execute(
                "UPDATE assistant_tool_attempts SET state='finished' WHERE id=%s", (attempt_id,)
            )
        resumed_claim = store.claim("second-worker")
        self.assertEqual(str(resumed_claim["id"]), second["id"])

    def test_cancelled_tool_does_not_restart_or_confirm_its_threaded_action(self):
        ticket = self.approved_ticket()
        handle = WorkspaceHandle(
            Path("/workspaces/threaded-project"), "/host/threaded-project", "fixture-config"
        )
        with patch.object(assistant.workspace, "require_workspace", return_value=handle), patch.object(
            assistant.workspace,
            "execution_status",
            return_value={"config_id": "fixture-config"},
        ):
            run = self.create_run(self.chat["id"], mode="Edit", ticket_id=ticket["id"])

        claimed = store.claim("thread-test-worker")
        self.assertEqual(str(claimed["id"]), run["id"])
        store.update(run["id"], "Running", "Worker started", restore_point={"before_ref": "fixture"})
        row = store.get_run(run["id"])
        tools = assistant.Runtime().tools(row, store.project(self.project["id"]))
        write_tool = next(tool for tool in tools if tool.name == "write_file")

        action_started = threading.Event()
        release_action = threading.Event()
        action_finished = threading.Event()
        action_calls = []

        def blocked_write(_root, path, content):
            action_calls.append((path, content))
            action_started.set()
            release_action.wait(timeout=5)
            action_finished.set()
            return {"path": path, "written": True}

        async def cancel_tool_call():
            tool_input = json.dumps(
                {"path": "src/sample.txt", "content": "fixture"}
            )
            tool_context = RunContextWrapper(None)
            tool_context.tool_name = write_tool.name
            tool_context._function_tool_arguments = write_tool.on_invoke_tool.prepare_arguments(
                tool_input, write_tool.name
            )
            with patch.object(assistant.workspace, "require_workspace", return_value=handle), patch.object(
                assistant.workspace, "write_file", side_effect=blocked_write
            ):
                task = asyncio.create_task(
                    write_tool.on_invoke_tool(
                        tool_context,
                        tool_input,
                    )
                )
                started = await asyncio.to_thread(action_started.wait, 2)
                self.assertTrue(started, "The mocked filesystem action did not start.")
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                self.assertTrue(store.uncertain(run["id"]))
                with connect() as conn:
                    attempt = conn.execute(
                        "SELECT state FROM assistant_tool_attempts WHERE run_id=%s",
                        (run["id"],),
                    ).fetchone()
                self.assertEqual(attempt["state"], "started")
                self.assertFalse(action_finished.is_set())
                release_action.set()
                finished = await asyncio.to_thread(action_finished.wait, 2)
                self.assertTrue(finished, "The canceled thread did not finish after release.")
                self.assertEqual(action_calls, [("src/sample.txt", "fixture")])
                self.assertTrue(store.uncertain(run["id"]))

        try:
            asyncio.run(cancel_tool_call())
        finally:
            release_action.set()


if __name__ == "__main__":
    unittest.main()
