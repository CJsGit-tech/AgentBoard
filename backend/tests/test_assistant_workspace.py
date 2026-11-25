import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from app.executor import ExecutorError, WorkspaceExecutor


def git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


@unittest.skipUnless(shutil.which("git"), "The isolated executor test suite requires host Git.")
class AssistantWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agentboard-workspace-test-")
        self.base = Path(self.temporary.name)
        self.host_root = self.base / "host-source"
        self.mount_root = self.base / "executor-mount"
        self.project_host = self.host_root / "Demo"
        self.project = self.mount_root / "Demo"
        self.project.mkdir(parents=True)
        self.host_root.mkdir(parents=True, exist_ok=True)
        for name, value in {
            "keep.txt": "baseline keep\n",
            "change.txt": "baseline change\n",
            "remove.txt": "baseline remove\n",
        }.items():
            (self.project / name).write_text(value, encoding="utf-8")
        git(self.project, "init", "-q", "-b", "main")
        git(self.project, "config", "user.name", "Fixture")
        git(self.project, "config", "user.email", "fixture@example.invalid")
        git(self.project, "add", "--", ".")
        git(self.project, "commit", "-qm", "fixture baseline")
        self.state = self.base / "executor-state"
        self.executor = WorkspaceExecutor(
            str(self.host_root), self.mount_root, os.getuid(), os.getgid(),
            socket_gid=(os.getgid() + 10001) % 65535,
            mount_checker=lambda host, target: (host == str(self.host_root) and target == str(self.mount_root.resolve()), "fixture-mount-evidence"),
            state_dir=self.state,
        )
        self.context = {
            "checkout_path": str(self.project_host),
            "config_id": hashlib.sha256(str(self.host_root).encode()).hexdigest(),
        }

    def tearDown(self):
        self.temporary.cleanup()

    def dispatch(self, operation: str, **values):
        return self.executor.dispatch({"operation": operation, **self.context, **values})

    def snapshot(self, run_id: str = "fixture-run") -> dict:
        return self.dispatch("snapshot", run_id=run_id)

    def test_mountinfo_matches_docker_desktop_fixture_and_rejects_wrong_folder(self):
        line = (
            "974 965 0:52 /tmp/assistant-delivery/executor-fixture /workspaces "
            "rw,nosuid,nodev,relatime - fakeowner /run/host_mark/private rw,fakeowner"
        )
        ok, evidence = self.executor._mount_check_from_lines(
            "/private/tmp/assistant-delivery/executor-fixture", "/workspaces", [line]
        )
        self.assertTrue(ok)
        self.assertIn("974", evidence)
        wrong, _ = self.executor._mount_check_from_lines(
            "/private/tmp/another-folder", "/workspaces", [line]
        )
        self.assertFalse(wrong)

    def test_non_git_read_and_list_keep_secret_and_ignore_filters(self):
        no_git = self.mount_root / "Plain"
        no_git.mkdir()
        (no_git / "visible.txt").write_text("visible", encoding="utf-8")
        (no_git / ".env").write_text("SECRET", encoding="utf-8")
        (no_git / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        (no_git / "ignored.txt").write_text("ignored", encoding="utf-8")
        host_plain = self.host_root / "Plain"
        no_git_context = {**self.context, "checkout_path": str(host_plain)}
        listed = self.executor.dispatch({"operation": "list_files", **no_git_context, "config_id": self.context["config_id"], "path": "."})
        self.assertIn("visible.txt", listed["files"])
        self.assertNotIn("ignored.txt", listed["files"])
        content = self.executor.dispatch({"operation": "read_file", **no_git_context, "config_id": self.context["config_id"], "path": "visible.txt"})
        import base64
        self.assertEqual(base64.b64decode(content["content_b64"]).decode(), "visible")
        with self.assertRaises(ExecutorError):
            self.executor.dispatch({"operation": "read_file", **no_git_context, "config_id": self.context["config_id"], "path": ".env"})

    def test_read_rejects_symlinks_secrets_and_git_ignored_paths(self):
        (self.project / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        (self.project / "ignored.txt").write_text("ignored", encoding="utf-8")
        outside = self.base / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        (self.project / "linked.txt").symlink_to(outside)
        with self.assertRaises(ExecutorError):
            self.dispatch("read_file", path=".env")
        with self.assertRaises(ExecutorError):
            self.dispatch("read_file", path="ignored.txt")
        with self.assertRaises(ExecutorError):
            self.dispatch("read_file", path="linked.txt")
        with self.assertRaises(ExecutorError):
            self.dispatch("read_file", path="../outside.txt")

    def test_write_respects_nested_directory_permissions(self):
        if os.geteuid() == 0:
            self.skipTest("Run this permission check as an unprivileged account.")
        nested = self.project / "restricted"
        nested.mkdir()
        locked = nested / "locked.txt"
        locked.write_text("do not replace\n", encoding="utf-8")
        git(self.project, "add", "--", "restricted/locked.txt")
        git(self.project, "commit", "-qm", "add restricted fixture")
        os.chmod(nested, 0o555)
        point = self.snapshot("permission-run")
        run_context = {**self.context, "run_id": point["run_id"]}
        import base64
        try:
            with self.assertRaises(ExecutorError):
                self.executor.dispatch({"operation": "write_file", **run_context, "path": "restricted/locked.txt",
                                        "content_b64": base64.b64encode(b"unauthorized\n").decode()})
            self.assertEqual(locked.read_text(), "do not replace\n")
        finally:
            os.chmod(nested, 0o755)

    def test_snapshot_selective_restore_preserves_unrelated_and_deleted_files(self):
        point = self.snapshot()
        run_context = {**self.context, "run_id": point["run_id"]}
        import base64
        self.executor.dispatch({"operation": "write_file", **run_context, "path": "change.txt",
                                "content_b64": base64.b64encode(b"assistant change\n").decode()})
        self.executor.dispatch({"operation": "delete_file", **run_context, "path": "remove.txt"})
        self.executor.dispatch({"operation": "write_file", **run_context, "path": "created.txt",
                                "content_b64": base64.b64encode(b"assistant created\n").decode()})
        (self.project / "unrelated.txt").write_text("later unrelated edit\n", encoding="utf-8")
        point = self.dispatch("finish_snapshot", point=point)
        self.assertEqual(point["changed_files"], ["change.txt", "created.txt", "remove.txt"])
        self.assertEqual(point["unowned_changes"], ["unrelated.txt"])
        preview = self.dispatch("restore_preview", point=point)
        self.assertEqual(preview["conflicts"], [])
        self.dispatch("restore", point=point)
        self.assertEqual((self.project / "change.txt").read_text(), "baseline change\n")
        self.assertEqual((self.project / "remove.txt").read_text(), "baseline remove\n")
        self.assertFalse((self.project / "created.txt").exists())
        self.assertEqual((self.project / "unrelated.txt").read_text(), "later unrelated edit\n")

    def test_failed_restore_preview_writes_nothing_on_conflict(self):
        point = self.snapshot("conflict-run")
        run_context = {**self.context, "run_id": point["run_id"]}
        import base64
        self.executor.dispatch({"operation": "write_file", **run_context, "path": "change.txt",
                                "content_b64": base64.b64encode(b"assistant change\n").decode()})
        self.executor.dispatch({"operation": "write_file", **run_context, "path": "created.txt",
                                "content_b64": base64.b64encode(b"assistant created\n").decode()})
        point = self.dispatch("finish_snapshot", point=point)
        (self.project / "change.txt").write_text("later user edit\n", encoding="utf-8")
        before_created = (self.project / "created.txt").read_text(encoding="utf-8")
        preview = self.dispatch("restore_preview", point=point)
        self.assertIn("change.txt", preview["conflicts"])
        with self.assertRaises(ExecutorError):
            self.dispatch("restore", point=point)
        self.assertEqual((self.project / "change.txt").read_text(encoding="utf-8"), "later user edit\n")
        self.assertEqual((self.project / "created.txt").read_text(encoding="utf-8"), before_created)

    def test_edit_refuses_a_file_changed_after_the_pre_run_snapshot(self):
        point = self.snapshot("concurrent-edit-run")
        (self.project / "change.txt").write_text("external user edit\n", encoding="utf-8")
        run_context = {**self.context, "run_id": point["run_id"]}
        import base64
        with self.assertRaises(ExecutorError):
            self.executor.dispatch({"operation": "write_file", **run_context, "path": "change.txt",
                                    "content_b64": base64.b64encode(b"assistant edit\n").decode()})
        self.assertEqual((self.project / "change.txt").read_text(), "external user edit\n")

    def test_preexisting_index_and_untracked_files_survive_restore(self):
        (self.project / "staged.txt").write_text("pre-existing staged\n", encoding="utf-8")
        (self.project / "untracked.txt").write_text("pre-existing untracked\n", encoding="utf-8")
        git(self.project, "add", "--", "staged.txt")
        index_before = hashlib.sha256((self.project / ".git" / "index").read_bytes()).hexdigest()
        point = self.snapshot("dirty-run")
        self.assertTrue(point["before_dirty"])
        run_context = {**self.context, "run_id": point["run_id"]}
        import base64
        self.executor.dispatch({"operation": "write_file", **run_context, "path": "change.txt",
                                "content_b64": base64.b64encode(b"assistant change\n").decode()})
        point = self.dispatch("finish_snapshot", point=point)
        self.assertEqual(point["changed_files"], ["change.txt"])
        self.dispatch("restore", point=point)
        self.assertEqual((self.project / "staged.txt").read_text(), "pre-existing staged\n")
        self.assertEqual((self.project / "untracked.txt").read_text(), "pre-existing untracked\n")
        index_after = hashlib.sha256((self.project / ".git" / "index").read_bytes()).hexdigest()
        self.assertEqual(index_before, index_after)

    def test_operation_receipt_prevents_replaying_a_completed_write(self):
        point = self.snapshot("receipt-run")
        operation_id = "operation-1"
        run_context = {**self.context, "run_id": point["run_id"], "operation_id": operation_id}
        import base64
        request = {"operation": "write_file", **run_context, "path": "change.txt",
                   "content_b64": base64.b64encode(b"receipt write\n").decode()}
        result = self.executor.dispatch(request)
        self.assertTrue(result["bytes"])
        receipt = self.executor.dispatch({"operation": "operation_receipt", **self.context,
                                         "operation_id": operation_id})
        self.assertEqual(receipt["status"], "completed")
        (self.project / "change.txt").write_text("later user edit\n", encoding="utf-8")
        self.executor.dispatch(request)
        self.assertEqual((self.project / "change.txt").read_text(), "later user edit\n")

    def test_run_check_is_busy_and_blocks_snapshot_while_active(self):
        script = self.project / "slow_check.py"
        script.write_text("import time\ntime.sleep(0.5)\n", encoding="utf-8")
        git(self.project, "add", "--", "slow_check.py")
        git(self.project, "commit", "-qm", "add check")
        outcome = {}

        def run():
            outcome.update(self.dispatch("run_check", argv=[sys.executable, "slow_check.py"]))

        worker = threading.Thread(target=run)
        worker.start()
        deadline = time.monotonic() + 2
        while not self.dispatch("is_idle")["active"] and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(self.dispatch("is_idle")["active"])
        with self.assertRaises(ExecutorError):
            self.snapshot("blocked-run")
        worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcome.get("exit_code"), 0)

    def test_verified_commit_refuses_dirty_baseline_and_commits_clean_run(self):
        (self.project / "preexisting.txt").write_text("do not commit\n", encoding="utf-8")
        dirty_point = self.snapshot("dirty-commit-run")
        run_context = {**self.context, "run_id": dirty_point["run_id"]}
        import base64
        self.executor.dispatch({"operation": "write_file", **run_context, "path": "change.txt",
                                "content_b64": base64.b64encode(b"run change\n").decode()})
        dirty_point = self.dispatch("finish_snapshot", point=dirty_point)
        blocked = self.dispatch("commit_verified", point=dirty_point, checks=[{"passed": True}])
        self.assertFalse(blocked["committed"])

        git(self.project, "restore", "--", "change.txt")
        (self.project / "preexisting.txt").unlink()
        clean = self.snapshot("clean-commit-run")
        clean_context = {**self.context, "run_id": clean["run_id"]}
        self.executor.dispatch({"operation": "write_file", **clean_context, "path": "change.txt",
                                "content_b64": base64.b64encode(b"verified run\n").decode()})
        clean = self.dispatch("finish_snapshot", point=clean)
        result = self.dispatch("commit_verified", point=clean, checks=[{"passed": True}])
        self.assertTrue(result["committed"], result)
        self.assertEqual(git(self.project, "status", "--porcelain"), "")


class SetupExecutionTests(unittest.TestCase):
    @unittest.skipUnless((Path(__file__).resolve().parents[2] / "scripts" / "setup-execution.py").is_file(),
                         "The setup helper is tested from the host checkout, not the API image.")
    def test_dry_run_prints_no_configuration_identifier_and_does_not_write(self):
        script = Path(__file__).resolve().parents[2] / "scripts" / "setup-execution.py"
        with tempfile.TemporaryDirectory(prefix="agentboard-setup-dry-run-") as folder:
            before = sorted(Path(folder).iterdir())
            result = subprocess.run([sys.executable, str(script), "--folder", folder, "--dry-run"],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("-> /workspaces", result.stdout)
            self.assertNotIn("Configuration ID:", result.stdout)
            self.assertEqual(sorted(Path(folder).iterdir()), before)


if __name__ == "__main__":
    unittest.main()
