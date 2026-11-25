"""Isolated local workspace executor.

This module has no AgentBoard, database, provider, or third-party imports. The
API talks to it through a permission-checked Unix socket. Project commands run
as the host user against only the selected /workspaces bind mount.
"""

from __future__ import annotations

import argparse
import base64
import fnmatch
import hashlib
import http.server
import json
import os
import re
import signal
import socket
import socketserver
import stat
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable


MAX_REQUEST_BYTES = 2_000_000
MAX_FILE_BYTES = 1_000_000
MAX_OUTPUT_BYTES = 1_000_000
MAX_SNAPSHOT_FILE_BYTES = 64 * 1024 * 1024
MAX_SNAPSHOT_TOTAL_BYTES = 256 * 1024 * 1024
MAX_LIST_FILES = 500
CHECK_TIMEOUT_SECONDS = 900
SAFE_PATH_PARTS = {".env", ".aws", ".ssh", ".gnupg", ".azure", ".config", ".npmrc", ".pypirc"}
SAFE_SECRET_NAMES = {
    "credentials", "credential", "secrets", "secret", "id_rsa", "id_ed25519",
    "id_ecdsa", "known_hosts", "authorized_keys", "service-account.json",
}
SAFE_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".keystore")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


class ExecutorError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _add_calendar_months(value: datetime, months: int) -> datetime:
    index = value.year * 12 + (value.month - 1) + months
    year, month_zero = divmod(index, 12)
    month = month_zero + 1
    import calendar

    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _decode_mount_field(value: str) -> str:
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)


class WorkspaceExecutor:
    def __init__(
        self,
        host_root: str | None = None,
        workspace_root: str | Path = "/workspaces",
        execution_uid: int | None = None,
        execution_gid: int | None = None,
        socket_gid: int = 10001,
        mount_checker: Callable[[str, str], tuple[bool, str]] | None = None,
        state_dir: str | Path | None = None,
    ) -> None:
        self.host_root = host_root or os.environ.get("AGENTBOARD_HOST_ROOT", "")
        self.workspace_root = Path(workspace_root).resolve(strict=False)
        self.execution_uid = int(execution_uid if execution_uid is not None else os.environ.get("AGENTBOARD_EXECUTION_UID", "65534"))
        self.execution_gid = int(execution_gid if execution_gid is not None else os.environ.get("AGENTBOARD_EXECUTION_GID", "65534"))
        self.socket_gid = socket_gid
        self._mount_checker = mount_checker or self._actual_mount_check
        self._guard = threading.RLock()
        self._write_locks: dict[str, threading.RLock] = {}
        self._active_jobs: dict[str, dict[str, Any]] = {}
        self.state_dir = Path(state_dir or os.environ.get("AGENTBOARD_EXECUTOR_STATE", "/var/lib/agentboard-executor"))
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.state_dir, 0o700)
        self._receipt_path = self.state_dir / "operations.json"
        self._receipt_lock = threading.RLock()
        self._receipts = self._load_receipts()
        self._run_path = self.state_dir / "runs.json"
        self._runs = self._load_runs()

    def _load_runs(self) -> dict[str, dict[str, Any]]:
        if not self._run_path.exists():
            return {}
        try:
            raw = json.loads(self._run_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            raise RuntimeError("Executor run metadata is unreadable.") from err
        if not isinstance(raw, dict) or any(not isinstance(value, dict) for value in raw.values()):
            raise RuntimeError("Executor run metadata has an invalid format.")
        return raw

    def _persist_mapping(self, path: Path, data: dict[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temporary = tempfile.mkstemp(prefix=f"{path.stem}-", suffix=".tmp", dir=self.state_dir)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, sort_keys=True, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(self.state_dir, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def _persist_runs(self) -> None:
        cutoff = _add_calendar_months(_now(), -2)
        self._runs = {
            key: value for key, value in self._runs.items()
            if datetime.fromisoformat(str(value.get("expires_at", _iso(_now()))).replace("Z", "+00:00")) >= cutoff
        }
        self._persist_mapping(self._run_path, self._runs)

    def _record_owned_path(self, payload: dict[str, Any], project_root: Path, repo: Path,
                           project_relative: str, path: str,
                           expected_digest: str | None) -> None:
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
            raise ExecutorError(409, "A run-scoped handle is required before changing files.")
        with self._receipt_lock:
            point = self._runs.get(run_id)
            if not point:
                raise ExecutorError(409, "Create this run's Git restore point before changing files.")
            if (point.get("checkout_path") != payload.get("checkout_path") or
                    point.get("config_id") != payload.get("config_id") or
                    point.get("project_path") != project_relative):
                raise ExecutorError(409, "This edit run belongs to a different workspace mapping.")
            before_tree = self._git(repo, ["rev-parse", "--verify", f"{point['before_ref']}^{{tree}}"]).decode().strip()
            if before_tree != point.get("before_tree"):
                raise ExecutorError(409, "The run's pre-edit Git restore point is missing or has changed.")
            if self._git(repo, ["rev-parse", "--verify", "HEAD"]).decode().strip() != point.get("head_before"):
                raise ExecutorError(409, "The project's Git branch changed while this edit run was active.")
            if path in point.get("owned_paths", []):
                current_digest = self._workspace_digest(project_root, path)
                if current_digest != point.get("owned_digests", {}).get(path):
                    raise ExecutorError(409, "This run's file changed after its last confirmed tool write.")
            else:
                baseline = self._tree_state(repo, point["before_tree"], project_relative, [path])
                current_tree, temporary_index = self._tree_from_paths(
                    repo, point["before_tree"], project_relative, [path],
                )
                try:
                    current = self._tree_state(repo, current_tree, project_relative, [path])
                finally:
                    temporary_index.unlink(missing_ok=True)
                if current != baseline:
                    raise ExecutorError(409, "This file changed after the run's restore point was created.")
            paths = set(point.get("owned_paths", []))
            paths.add(path)
            point["owned_paths"] = sorted(paths)
            digests = dict(point.get("owned_digests", {}))
            digests[path] = expected_digest
            point["owned_digests"] = digests
            self._persist_runs()

    def _run_metadata(self, payload: dict[str, Any], project_relative: str,
                      run_id: str | None = None) -> dict[str, Any]:
        run_id = run_id or payload.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
            raise ExecutorError(422, "Use a run-scoped workspace handle for this operation.")
        with self._receipt_lock:
            point = self._runs.get(run_id)
            if not point or point.get("checkout_path") != payload.get("checkout_path") or point.get("config_id") != payload.get("config_id") or point.get("project_path") != project_relative:
                raise ExecutorError(409, "This edit run has no matching Git restore point.")
            if point.get("before_ref") != self._ref(run_id, "before"):
                raise ExecutorError(409, "The run's pre-edit Git restore point is invalid.")
            try:
                tree = self._git(Path(point["repo_path"]) if Path(point["repo_path"]).is_absolute()
                                 else self.workspace_root / point["repo_path"],
                                 ["rev-parse", "--verify", f"{point['before_ref']}^{{tree}}"]).decode().strip()
            except (KeyError, ExecutorError) as err:
                raise ExecutorError(409, "The run's pre-edit Git restore point is missing.") from err
            if tree != point.get("before_tree"):
                raise ExecutorError(409, "The run's pre-edit Git restore point has changed.")
        return point

    def _load_receipts(self) -> dict[str, dict[str, Any]]:
        if not self._receipt_path.exists():
            return {}
        try:
            raw = json.loads(self._receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            raise RuntimeError("Executor operation receipt store is unreadable.") from err
        if not isinstance(raw, dict) or any(not isinstance(value, dict) for value in raw.values()):
            raise RuntimeError("Executor operation receipt store has an invalid format.")
        return raw

    def _persist_receipts(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        cutoff = _add_calendar_months(_now(), -2)
        self._receipts = {
            key: value for key, value in self._receipts.items()
            if value.get("status") in ("started", "uncertain") or
            datetime.fromisoformat(str(value.get("started_at", _iso(_now()))).replace("Z", "+00:00")) >= cutoff
        }
        fd, temporary = tempfile.mkstemp(prefix="operations-", suffix=".tmp", dir=self.state_dir)
        try:
            os.fchmod(fd, 0o600)
            payload = json.dumps(self._receipts, sort_keys=True, separators=(",", ":")).encode("utf-8")
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self._receipt_path)
            directory_fd = os.open(self.state_dir, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _operation_digest(payload: dict[str, Any]) -> str:
        clean = {key: value for key, value in payload.items() if key != "operation_id"}
        body = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    def _receipt_key(self, operation_id: str) -> str:
        if not isinstance(operation_id, str) or not RUN_ID_RE.fullmatch(operation_id):
            raise ExecutorError(422, "Use a safe operation identifier for recovery.")
        return operation_id

    def _with_receipt(self, operation: str, payload: dict[str, Any], handler: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
        operation_id = self._receipt_key(payload["operation_id"])
        digest = self._operation_digest(payload)
        with self._receipt_lock:
            existing = self._receipts.get(operation_id)
            if existing:
                if existing.get("request_digest") != digest:
                    raise ExecutorError(409, "This operation ID was already used for a different request.")
                if existing.get("status") == "completed":
                    if existing.get("summary_only"):
                        summary = dict(existing.get("result", {}))
                        return {**summary, "output": "[Recovered check result; full output was not retained.]", "recovered": True}
                    return dict(existing.get("result", {}))
                if existing.get("status") == "failed":
                    raise ExecutorError(int(existing.get("error_status", 409)), str(existing.get("error", "The earlier operation failed.")))
                raise ExecutorError(409, "This operation has an uncertain outcome. Reconcile it before continuing; it will not be replayed.")
            receipt = {
                "operation_id": operation_id, "operation": operation,
                "request_digest": digest, "workspace_key": self._workspace_key(
                    str(payload.get("checkout_path", "")), str(payload.get("config_id", ""))),
                "status": "started", "started_at": _iso(_now()),
            }
            self._receipts[operation_id] = receipt
            self._persist_receipts()
        try:
            result = handler(payload)
        except Exception as err:
            with self._receipt_lock:
                receipt = self._receipts[operation_id]
                receipt.update(status="uncertain", finished_at=_iso(_now()),
                               error_type=type(err).__name__)
                self._persist_receipts()
            raise
        summary_only = operation == "run_check"
        if summary_only:
            safe_result = {key: result[key] for key in ("exit_code", "passed", "output_truncated") if key in result}
        else:
            safe_result = result
        with self._receipt_lock:
            receipt = self._receipts[operation_id]
            receipt.update(status="completed", finished_at=_iso(_now()),
                           summary_only=summary_only, result=safe_result)
            self._persist_receipts()
        return result

    def _operation_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, _config_id, _evidence, key = self._context(payload)
        operation_id = self._receipt_key(payload.get("operation_id"))
        with self._receipt_lock, self._guard:
            record = self._receipts.get(operation_id)
            if not record or record.get("workspace_key") != key:
                return {"operation_id": operation_id, "status": "not_found"}
            result = dict(record)
            if result.get("status") == "started" and key not in self._active_jobs:
                result["status"] = "uncertain"
            result.pop("request_digest", None)
            result.pop("workspace_key", None)
            return result

    def _actual_mount_check(self, host_root: str, workspace_root: str) -> tuple[bool, str]:
        try:
            lines = Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
        except OSError:
            return False, "Mount information is unavailable inside the executor."
        return self._mount_check_from_lines(host_root, workspace_root, lines)

    @staticmethod
    def _mount_check_from_lines(host_root: str, workspace_root: str, lines: list[str]) -> tuple[bool, str]:
        for line in lines:
            fields = line.split(" - ", 1)
            if len(fields) != 2:
                continue
            left, right = fields
            mount_fields = left.split()
            fs_fields = right.split()
            if len(mount_fields) < 6 or len(fs_fields) < 3:
                continue
            mount_root = _decode_mount_field(mount_fields[3])
            target = _decode_mount_field(mount_fields[4])
            if os.path.normpath(target) != os.path.normpath(workspace_root):
                continue
            source = _decode_mount_field(fs_fields[1])
            configured = os.path.normpath(host_root)
            root_path = os.path.normpath(mount_root)
            actual = os.path.normpath(source)
            desktop_root = root_path.removeprefix("/host_mnt")
            desktop_source = actual.removeprefix("/host_mnt")
            host_marker = re.search(r"/run/host_mark(/[^ ]*)$", actual)
            marker_match = False
            if host_marker:
                host_prefix = os.path.normpath(host_marker.group(1))
                candidate = os.path.normpath(os.path.join(host_prefix, root_path.lstrip("/")))
                marker_match = candidate == configured
            matches = (
                root_path == configured or desktop_root == configured or
                actual == configured or desktop_source == configured or marker_match
            )
            if not matches:
                return False, "The mounted folder does not match the selected host folder. Restart required."
            if "ro" in mount_fields[5].split(",") or "ro" in fs_fields[2].split(","):
                return False, "The selected folder is mounted read only."
            return True, f"{mount_fields[0]}:{mount_root}:{target}:{source}"
        return False, "The selected host folder is not mounted at /workspaces. Restart required."

    def _host_mount_state(self) -> tuple[bool, str, str]:
        if not self.host_root:
            return False, "", "Choose a host folder and apply local execution setup."
        configured = os.path.normpath(self.host_root)
        config_id = hashlib.sha256(configured.encode("utf-8")).hexdigest()
        expected_config_id = os.environ.get("AGENTBOARD_EXECUTOR_CONFIG_ID")
        if expected_config_id and expected_config_id != config_id:
            return False, config_id, "Executor configuration does not match the selected folder. Restart required."
        ok, evidence = self._mount_checker(configured, str(self.workspace_root))
        if not ok:
            return False, config_id, evidence
        try:
            details = self.workspace_root.stat()
            if not stat.S_ISDIR(details.st_mode):
                return False, evidence, "The mounted workspace root is not a directory. Restart required."
        except OSError:
            return False, evidence, "The mounted workspace folder is unavailable. Restart required."
        return True, config_id, evidence

    def _project_mapping(self, checkout_path: str) -> tuple[Path, str, str, str]:
        ready, config_id, evidence = self._host_mount_state()
        if not ready:
            status = "Not configured" if not self.host_root else "Restart required"
            raise ExecutorError(409, f"{status}: {evidence}")
        if not isinstance(checkout_path, str) or not checkout_path or "\x00" in checkout_path:
            raise ExecutorError(422, "This project has no usable checkout folder.")
        requested = Path(checkout_path)
        if not requested.is_absolute() or any(part == ".." for part in requested.parts):
            raise ExecutorError(422, "Use an absolute project folder inside the selected host folder.")
        host_root = Path(os.path.normpath(self.host_root))
        normalized = Path(os.path.normpath(checkout_path))
        try:
            relative = normalized.relative_to(host_root)
        except ValueError as err:
            raise ExecutorError(409, "The project checkout is outside the selected host folder.") from err
        if relative == Path("."):
            relative = Path()
        project_candidate = self.workspace_root.joinpath(*relative.parts)
        if not project_candidate.exists() or not project_candidate.is_dir():
            raise ExecutorError(409, "The project folder is missing from the selected host mount.")
        self._reject_symlink_components(self.workspace_root, project_candidate)
        project_root = project_candidate.resolve(strict=True)
        return project_root, str(relative.as_posix() if relative.parts else "."), config_id, evidence

    @staticmethod
    def _reject_symlink_components(root: Path, target: Path) -> None:
        try:
            rel = target.relative_to(root)
        except ValueError as err:
            raise ExecutorError(422, "The requested path is outside the selected workspace.") from err
        current = root
        for part in rel.parts:
            if part in ("", ".", ".."):
                raise ExecutorError(422, "The requested path is not a safe workspace path.")
            current = current / part
            try:
                if current.is_symlink():
                    raise ExecutorError(422, "Symbolic links are not available to Assistant file tools.")
            except OSError as err:
                raise ExecutorError(409, "The project folder is unavailable.") from err

    def _verify_context(self, payload: dict[str, Any]) -> tuple[Path, str, str, str]:
        project_root, relative, config_id, evidence = self._project_mapping(payload.get("checkout_path", ""))
        supplied = payload.get("config_id")
        if supplied and supplied != config_id:
            raise ExecutorError(409, "Local execution changed after this run started. Reload setup and retry.")
        return project_root, relative, config_id, evidence

    def status(self, checkout_path: str) -> dict[str, Any]:
        if not self.host_root:
            return self._status("Not configured", "", "", "Choose a host folder and apply local execution setup.")
        try:
            project_root, _, config_id, _evidence = self._project_mapping(checkout_path)
            if not self._runner_access(project_root, os.R_OK | os.W_OK | os.X_OK):
                return self._status("Unavailable", self.host_root, str(project_root),
                                    "The executor user cannot read and write this project folder.", config_id)
            return self._status("Ready", self.host_root, str(project_root),
                                "The selected project folder is mounted and available.", config_id)
        except ExecutorError as err:
            message = str(err)
            status = "Restart required" if "Restart required" in message else "Unavailable"
            if "outside the selected host folder" in message:
                status = "Unavailable"
            return self._status(status, self.host_root, "", message)

    @staticmethod
    def _status(status: str, host_folder: str, project_path: str, message: str,
                config_id: str = "") -> dict[str, Any]:
        return {
            "status": status, "host_folder": host_folder, "container_folder": "/workspaces",
            "project_path": project_path, "access": "read/write", "message": message,
            "setup_command": "python3 scripts/setup-execution.py --folder <folder> --dry-run",
            "config_id": config_id,
        }

    def _runner_access(self, path: Path, mode: int) -> bool:
        code = "import os,sys; sys.exit(0 if os.access(sys.argv[1], int(sys.argv[2])) else 1)"
        result = self._run_as_executor_user(
            [sys.executable, "-c", code, str(path), str(mode)], cwd=self.workspace_root,
            timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0

    def _identity_kwargs(self) -> dict[str, Any]:
        if os.geteuid() == 0:
            return {"user": self.execution_uid, "group": self.execution_gid, "extra_groups": []}
        if self.execution_uid != os.getuid() or self.execution_gid != os.getgid():
            raise ExecutorError(503, "The executor cannot assume the selected host user's permissions.")
        return {}

    def _file_worker(self, project_root: Path, request: dict[str, Any]) -> dict[str, Any]:
        env = self._safe_env(project_root)
        env["AGENTBOARD_WORKSPACE_ROOT"] = str(self.workspace_root)
        body = json.dumps(request, separators=(",", ":")).encode("utf-8")
        result = self._run_as_executor_user(
            [sys.executable, str(Path(__file__).resolve()), "--file-operation"],
            cwd=project_root, timeout=120, env=env, input=body,
        )
        try:
            response = json.loads(result.stdout or b"{}")
        except json.JSONDecodeError as err:
            raise ExecutorError(503, "The workspace permission helper returned an invalid response.") from err
        if result.returncode != 0:
            raise ExecutorError(int(response.get("status", 422)), str(response.get("detail", "The file operation was denied.")))
        if not isinstance(response, dict):
            raise ExecutorError(503, "The workspace permission helper returned an invalid response.")
        return response

    def _safe_env(self, workspace: Path) -> dict[str, str]:
        return {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME": "/tmp/agentboard-executor-home", "TMPDIR": "/tmp",
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PWD": str(workspace),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
        }

    def _run_as_executor_user(self, argv: list[str], cwd: Path, timeout: int = 60,
                              stdout: Any = subprocess.PIPE, stderr: Any = subprocess.PIPE,
                              env: dict[str, str] | None = None, **kwargs: Any) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                argv, cwd=str(cwd), env=env or self._safe_env(cwd), stdout=stdout, stderr=stderr,
                timeout=timeout, check=False, **self._identity_kwargs(), **kwargs,
            )
        except FileNotFoundError as err:
            raise ExecutorError(422, f"Required command is not installed: {argv[0]}") from err
        except subprocess.TimeoutExpired as err:
            raise ExecutorError(504, "The local workspace operation timed out.") from err

    def _git(self, repo: Path, args: list[str], timeout: int = 120,
             index_file: Path | None = None) -> bytes:
        env = self._safe_env(repo)
        env["GIT_LITERAL_PATHSPECS"] = "1"
        if index_file:
            env["GIT_INDEX_FILE"] = str(index_file)
        result = self._run_as_executor_user(
            ["git", "-C", str(repo), *args], cwd=repo, timeout=timeout,
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            stderr = (result.stderr or b"").decode("utf-8", "replace").strip()
            safe_detail = stderr[-1000:] or "Git operation failed."
            raise ExecutorError(409, safe_detail)
        return result.stdout or b""

    def _repository(self, project_root: Path) -> tuple[Path, str, str]:
        top = Path(self._git(project_root, ["rev-parse", "--show-toplevel"]).decode().strip()).resolve(strict=True)
        try:
            top.relative_to(self.workspace_root.resolve(strict=True))
        except ValueError as err:
            raise ExecutorError(409, "Git metadata is outside the selected execution mount.") from err
        common_raw = self._git(project_root, ["rev-parse", "--git-common-dir"]).decode().strip()
        common = Path(common_raw)
        if not common.is_absolute():
            common = top / common
        common = common.resolve(strict=True)
        try:
            common.relative_to(self.workspace_root.resolve(strict=True))
        except ValueError as err:
            raise ExecutorError(409, "Git metadata is outside the selected execution mount.") from err
        self._reject_symlink_components(self.workspace_root.resolve(strict=True), top)
        project_relative = project_root.relative_to(top).as_posix()
        if project_relative == ".":
            project_relative = ""
        head = self._git(top, ["rev-parse", "--verify", "HEAD"]).decode().strip()
        return top, project_relative, head

    def _optional_repository(self, project_root: Path) -> tuple[Path, str] | None:
        env = self._safe_env(project_root)
        result = self._run_as_executor_user(
            ["git", "-C", str(project_root), "rev-parse", "--show-toplevel"],
            cwd=project_root, timeout=30, env=env,
        )
        if result.returncode != 0:
            error = (result.stderr or b"").decode("utf-8", "replace").lower()
            if "not a git repository" in error or "outside a repository" in error:
                return None
            raise ExecutorError(409, "Git could not verify this project folder.")
        top = Path(result.stdout.decode().strip()).resolve(strict=True)
        try:
            top.relative_to(self.workspace_root.resolve(strict=True))
        except ValueError as err:
            raise ExecutorError(409, "Git metadata is outside the selected execution mount.") from err
        common_raw = self._git(project_root, ["rev-parse", "--git-common-dir"]).decode().strip()
        common = Path(common_raw)
        if not common.is_absolute():
            common = top / common
        try:
            common.resolve(strict=True).relative_to(self.workspace_root.resolve(strict=True))
        except (OSError, ValueError) as err:
            raise ExecutorError(409, "Git metadata is outside the selected execution mount.") from err
        relative = project_root.relative_to(top).as_posix()
        return top, "" if relative == "." else relative

    def _status_paths(self, repo: Path, head: str, project_relative: str) -> list[str]:
        args = ["status", "--porcelain=v1", "-z", "--untracked-files=all"]
        if project_relative:
            args.extend(["--", project_relative])
        return [entry.decode("utf-8", "surrogateescape") for entry in self._git(repo, args).split(b"\0") if entry]

    def _pathspec(self, project_relative: str) -> list[str]:
        return ["--", project_relative] if project_relative else ["--", "."]

    def _dirty_size(self, repo: Path, project_root: Path, head: str, project_relative: str) -> None:
        paths = set()
        paths.update(self._git(repo, ["diff", "--name-only", "-z", "HEAD", *self._pathspec(project_relative)]).decode("utf-8", "surrogateescape").split("\0"))
        paths.update(self._git(repo, ["ls-files", "--others", "--exclude-standard", "-z", *self._pathspec(project_relative)]).decode("utf-8", "surrogateescape").split("\0"))
        total = 0
        for rel in filter(None, paths):
            path = repo / rel
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode):
                size = len(os.readlink(path).encode("utf-8", "surrogateescape"))
            elif stat.S_ISREG(info.st_mode):
                size = info.st_size
            else:
                continue
            if size > MAX_SNAPSHOT_FILE_BYTES:
                raise ExecutorError(413, f"Git snapshot exceeds the per-file limit: {rel}")
            total += size
            if total > MAX_SNAPSHOT_TOTAL_BYTES:
                raise ExecutorError(413, "Git snapshot exceeds the 256 MiB dirty-file limit.")

    def _temp_index(self) -> Path:
        fd, name = tempfile.mkstemp(prefix="agentboard-index-", suffix=".tmp", dir="/tmp")
        os.fchmod(fd, 0o644)
        if os.geteuid() == 0:
            os.fchown(fd, self.execution_uid, self.execution_gid)
        os.close(fd)
        os.unlink(name)
        return Path(name)

    def _tree_from_worktree(self, repo: Path, head: str, project_relative: str) -> tuple[str, Path]:
        index = self._temp_index()
        try:
            self._git(repo, ["read-tree", head], index_file=index)
            self._git(repo, ["add", "-A", *self._pathspec(project_relative)], timeout=300, index_file=index)
            tree = self._git(repo, ["write-tree"], index_file=index).decode().strip()
            return tree, index
        except Exception:
            index.unlink(missing_ok=True)
            raise

    def _tree_from_paths(self, repo: Path, base_tree: str, project_relative: str,
                         paths: list[str]) -> tuple[str, Path]:
        index = self._temp_index()
        try:
            self._git(repo, ["read-tree", base_tree], index_file=index)
            base_entries = self._tree_entries(repo, base_tree, project_relative)
            repo_paths = []
            for path in paths:
                parts = self._parts(path)
                rel = "/".join(parts)
                if project_relative:
                    rel = f"{project_relative}/{rel}"
                # `git add -A -- path` errors for a path that is both absent
                # from the worktree and absent from the index. That is the
                # normal state for a new file before the write helper runs.
                # Keep the base tree unchanged in that case. Tracked paths
                # still go through git add when deleted, so deletion is
                # recorded in the temporary index.
                project_path = path
                if os.path.lexists(repo / rel) or project_path in base_entries:
                    repo_paths.append(rel)
            if repo_paths:
                self._git(repo, ["add", "-A", "--", *repo_paths], timeout=300, index_file=index)
            tree = self._git(repo, ["write-tree"], index_file=index).decode().strip()
            return tree, index
        except Exception:
            index.unlink(missing_ok=True)
            raise

    def _commit_tree(self, repo: Path, tree: str, parent: str, run_id: str) -> str:
        env = self._safe_env(repo)
        env.update({
            "GIT_AUTHOR_NAME": "AgentBoard Assistant", "GIT_AUTHOR_EMAIL": "assistant@agentboard.local",
            "GIT_COMMITTER_NAME": "AgentBoard Assistant", "GIT_COMMITTER_EMAIL": "assistant@agentboard.local",
        })
        result = self._run_as_executor_user(
            ["git", "-C", str(repo), "commit-tree", tree, "-p", parent], cwd=repo,
            timeout=120, env=env, input=f"AgentBoard assistant restore point {run_id}\n".encode(),
        )
        if result.returncode != 0:
            raise ExecutorError(409, (result.stderr or b"").decode("utf-8", "replace")[-1000:] or "Could not save Git restore point.")
        return result.stdout.decode().strip()

    def _ref(self, run_id: str, phase: str) -> str:
        if not RUN_ID_RE.fullmatch(run_id):
            raise ExecutorError(422, "Use a safe run identifier for Git recovery.")
        return f"refs/agentboard/assistant/{run_id}/{phase}"

    def _set_ref(self, repo: Path, ref: str, commit: str) -> None:
        self._git(repo, ["update-ref", ref, commit])

    def _ensure_not_busy(self, workspace_key: str) -> None:
        with self._guard:
            if workspace_key in self._active_jobs:
                raise ExecutorError(409, "A workspace check is still running. Wait for it before snapshot or restore.")

    def _lock(self, workspace_key: str) -> threading.RLock:
        with self._guard:
            return self._write_locks.setdefault(workspace_key, threading.RLock())

    @staticmethod
    def _workspace_key(checkout_path: str, config_id: str) -> str:
        return hashlib.sha256(f"{checkout_path}\0{config_id}".encode()).hexdigest()

    def _context(self, payload: dict[str, Any]) -> tuple[Path, str, str, str, str]:
        project_root, project_relative, config_id, evidence = self._verify_context(payload)
        checkout_path = str(payload["checkout_path"])
        key = self._workspace_key(checkout_path, config_id)
        return project_root, project_relative, config_id, evidence, key

    def _snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, project_relative, config_id, _evidence, key = self._context(payload)
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
            raise ExecutorError(422, "Use a safe run identifier for Git recovery.")
        self._ensure_not_busy(key)
        with self._lock(key):
            repo, repo_project_relative, head = self._repository(project_root)
            before_ref, after_ref = self._ref(run_id, "before"), self._ref(run_id, "after")
            existing = self._run_as_executor_user(
                ["git", "-C", str(repo), "show-ref", "--verify", "--quiet", before_ref],
                cwd=repo, timeout=30, env=self._safe_env(repo), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if existing.returncode == 0:
                raise ExecutorError(409, "A restore point already exists for this run.")
            self._dirty_size(repo, project_root, head, repo_project_relative)
            dirty_paths = self._status_paths(repo, head, repo_project_relative)
            tree, index = self._tree_from_worktree(repo, head, repo_project_relative)
            try:
                commit = self._commit_tree(repo, tree, head, run_id)
                self._set_ref(repo, before_ref, commit)
            finally:
                index.unlink(missing_ok=True)
            created = _now()
            point = {
                "run_id": run_id, "before_ref": before_ref, "before_tree": tree,
                "after_ref": after_ref, "repo_path": str(repo.relative_to(self.workspace_root)),
                "project_path": repo_project_relative, "checkout_path": str(payload["checkout_path"]),
                "config_id": config_id, "head_before": head, "before_dirty": bool(dirty_paths),
                "before_dirty_paths": dirty_paths, "created_at": _iso(created),
                "expires_at": _iso(_add_calendar_months(created, 2)),
            }
            with self._receipt_lock:
                if run_id in self._runs:
                    raise ExecutorError(409, "A restore point already exists for this run.")
                self._runs[run_id] = {
                    "run_id": run_id, "checkout_path": str(payload["checkout_path"]),
                    "config_id": config_id, "project_path": repo_project_relative,
                    "repo_path": str(repo.relative_to(self.workspace_root)),
                    "before_ref": before_ref, "before_tree": tree, "head_before": head,
                    "owned_paths": [], "owned_digests": {}, "created_at": point["created_at"],
                    "expires_at": point["expires_at"],
                }
                self._persist_runs()
            point["owned_paths"] = []
            point["unowned_changes"] = []
            return point

    def _point_repo(self, project_root: Path, project_relative: str, point: dict[str, Any], checkout: str,
                    config_id: str) -> tuple[Path, str, str, str]:
        if not isinstance(point, dict):
            raise ExecutorError(422, "The restore point is invalid.")
        run_id = point.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
            raise ExecutorError(422, "The restore point is invalid.")
        if point.get("checkout_path") != checkout or point.get("config_id") != config_id:
            raise ExecutorError(409, "The restore point belongs to a different workspace mapping.")
        repo, repo_project_relative, _head = self._repository(project_root)
        repo_path = str(repo.relative_to(self.workspace_root))
        if point.get("repo_path") != repo_path or point.get("project_path") != repo_project_relative:
            raise ExecutorError(409, "The project Git mapping changed after this restore point was created.")
        before_ref, after_ref = self._ref(run_id, "before"), self._ref(run_id, "after")
        if point.get("before_ref") != before_ref or point.get("after_ref") != after_ref:
            raise ExecutorError(422, "The restore point reference is invalid.")
        return repo, repo_project_relative, before_ref, after_ref

    def _finish_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, config_id, _evidence, key = self._context(payload)
        self._ensure_not_busy(key)
        with self._lock(key):
            point = payload.get("point")
            repo, project_relative, before_ref, after_ref = self._point_repo(
                project_root, _relative, point, str(payload["checkout_path"]), config_id,
            )
            head = self._git(repo, ["rev-parse", "--verify", "HEAD"]).decode().strip()
            self._dirty_size(repo, project_root, head, project_relative)
            run_meta = self._run_metadata(payload, project_relative, str(point["run_id"]))
            owned_paths = sorted(run_meta.get("owned_paths", []))
            digests = run_meta.get("owned_digests", {})
            accepted_paths = []
            unowned = []
            for path in owned_paths:
                expected = digests.get(path)
                current = self._workspace_digest(project_root, path)
                if current == expected:
                    accepted_paths.append(path)
                else:
                    unowned.append(path)
            after_tree, index = self._tree_from_paths(
                repo, str(point["before_tree"]), project_relative, accepted_paths,
            )
            try:
                commit = self._commit_tree(repo, after_tree, str(point["head_before"]), point["run_id"] + "-after")
                self._set_ref(repo, after_ref, commit)
            finally:
                index.unlink(missing_ok=True)
            changed = self._changed_paths(repo, point["before_tree"], after_tree, project_relative)
            actual_tree, actual_index = self._tree_from_worktree(repo, head, project_relative)
            try:
                unowned.extend(self._changed_paths(repo, after_tree, actual_tree, project_relative))
            finally:
                actual_index.unlink(missing_ok=True)
            unowned = sorted(set(unowned) - set(accepted_paths))
            finished_at = _iso(_now())
            result = {**point, "owned_paths": owned_paths, "after_tree": after_tree,
                      "after_commit": commit, "changed_files": changed,
                      "unowned_changes": unowned, "finished_at": finished_at}
            with self._receipt_lock:
                run_meta.update(after_tree=after_tree, after_ref=after_ref,
                                changed_files=changed, unowned_changes=unowned,
                                finished_at=finished_at)
                self._persist_runs()
            return result

    def _workspace_digest(self, project_root: Path, path: str) -> str | None:
        result = self._file_worker(project_root, {
            "operation": "digest", "workspace": str(self.workspace_root),
            "project_root": str(project_root), "path": path,
        })
        return result.get("digest")

    def _changed_paths(self, repo: Path, before_tree: str, after_tree: str, project_relative: str) -> list[str]:
        out = self._git(repo, ["diff", "--no-renames", "--name-only", "-z", before_tree, after_tree,
                               *self._pathspec(project_relative)])
        paths = [item.decode("utf-8", "surrogateescape") for item in out.split(b"\0") if item]
        prefix = project_relative + "/" if project_relative else ""
        scoped = []
        for rel in paths:
            if prefix and not rel.startswith(prefix):
                continue
            scoped.append(rel[len(prefix):] if prefix else rel)
        return sorted(scoped)

    def _tree_entries(self, repo: Path, tree: str, project_relative: str) -> dict[str, tuple[str, str, str]]:
        args = ["ls-tree", "-r", "-z", "--full-tree", tree, *self._pathspec(project_relative)]
        raw = self._git(repo, args)
        entries: dict[str, tuple[str, str, str]] = {}
        prefix = project_relative + "/" if project_relative else ""
        for item in raw.split(b"\0"):
            if not item:
                continue
            metadata, rel = item.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split()
            name = rel.decode("utf-8", "surrogateescape")
            if prefix:
                if name == project_relative:
                    name = ""
                elif name.startswith(prefix):
                    name = name[len(prefix):]
                else:
                    continue
            entries[name] = (mode, kind, oid)
        return entries

    def _current_tree(self, repo: Path, head: str, project_relative: str) -> tuple[str, Path]:
        self._dirty_size(repo, repo, head, project_relative)
        return self._tree_from_worktree(repo, head, project_relative)

    def _fallback_ignored(self, project_root: Path, path: str) -> bool:
        target = project_root.joinpath(*self._parts(path))
        ignored = False
        ancestors = [project_root]
        current = project_root
        for part in PurePosixPath(path).parts[:-1]:
            current = current / part
            ancestors.append(current)
        for directory in ancestors:
            rule_file = directory / ".gitignore"
            try:
                if rule_file.is_symlink():
                    raise ExecutorError(422, "Symbolic ignore files are not supported.")
                rules = rule_file.read_text(encoding="utf-8").splitlines()
            except FileNotFoundError:
                continue
            except UnicodeDecodeError as err:
                raise ExecutorError(422, "The project ignore file is not valid UTF-8.") from err
            except OSError as err:
                raise ExecutorError(422, "The project ignore rules cannot be read.") from err
            try:
                relative = target.relative_to(directory).as_posix()
            except ValueError:
                continue
            for raw in rules:
                rule = raw.strip()
                if not rule or rule.startswith("#"):
                    continue
                negate = rule.startswith("!")
                if negate:
                    rule = rule[1:]
                directory_only = rule.endswith("/")
                rule = rule.strip("/")
                if not rule:
                    continue
                if "/" in rule:
                    matched = fnmatch.fnmatchcase(relative, rule)
                else:
                    matched = any(fnmatch.fnmatchcase(part, rule) for part in PurePosixPath(relative).parts)
                if directory_only:
                    matched = matched and target.is_dir()
                if matched:
                    ignored = not negate
        return ignored

    def _ignored(self, repo: Path | None, project_relative: str, path: str,
                 project_root: Path | None = None) -> bool:
        if repo is None:
            if project_root is None:
                raise ExecutorError(422, "The project folder is unavailable.")
            return self._fallback_ignored(project_root, path)
        combined = f"{project_relative}/{path}" if project_relative else path
        env = self._safe_env(repo)
        result = self._run_as_executor_user(
            ["git", "-C", str(repo), "check-ignore", "-q", "-z", "--stdin"],
            cwd=repo, timeout=20, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            input=combined.encode("utf-8", "surrogateescape") + b"\0",
        )
        if result.returncode == 0:
            return True
        if result.returncode == 1:
            return False
        raise ExecutorError(409, "Git could not verify whether this path is ignored.")

    @staticmethod
    def _parts(value: str, allow_dot: bool = False) -> tuple[str, ...]:
        if not isinstance(value, str) or "\x00" in value or len(value.encode("utf-8", "surrogateescape")) > 4096:
            raise ExecutorError(422, "Use a short relative file path.")
        if value in ("", ".") and allow_dot:
            return ()
        path = PurePosixPath(value)
        parts = path.parts
        if path.is_absolute() or not parts or any(part in (".", "..", "") for part in parts):
            raise ExecutorError(422, "Use a relative file path inside the selected project.")
        if any(part.lower() == ".git" for part in parts):
            raise ExecutorError(422, "Git metadata is not available to Assistant file tools.")
        for part in parts:
            lowered = part.lower()
            if lowered in SAFE_PATH_PARTS or lowered in SAFE_SECRET_NAMES or lowered.startswith(".env."):
                raise ExecutorError(422, "Secret and credential paths are not available to Assistant file tools.")
            if lowered.endswith(SAFE_SECRET_SUFFIXES):
                raise ExecutorError(422, "Secret and credential files are not available to Assistant file tools.")
        return tuple(parts)

    def _open_directory(self, project_root: Path, parts: tuple[str, ...]) -> int:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            current_fd = os.open(project_root, flags)
        except OSError as err:
            raise ExecutorError(409, "The project folder cannot be opened safely.") from err
        try:
            for part in parts:
                next_fd = os.open(part, flags, dir_fd=current_fd)
                os.close(current_fd)
                current_fd = next_fd
            return current_fd
        except OSError as err:
            os.close(current_fd)
            raise ExecutorError(422, "A parent path is missing or is a symbolic link.") from err

    def _assert_file_path(self, repo: Path | None, project_relative: str, path: str,
                          project_root: Path | None = None) -> tuple[str, ...]:
        parts = self._parts(path)
        if self._ignored(repo, project_relative, path, project_root):
            raise ExecutorError(422, "Ignored files are not available to Assistant file tools.")
        return parts

    def _read_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, project_relative, _config_id, _evidence, _key = self._context(payload)
        repository = self._optional_repository(project_root)
        repo, git_project_relative = repository if repository else (None, "")
        path = payload.get("path")
        self._assert_file_path(repo, git_project_relative, path, project_root)
        result = self._file_worker(project_root, {
            "operation": "read", "workspace": str(self.workspace_root),
            "project_root": str(project_root), "path": path,
        })
        content = base64.b64decode(result["content_b64"], validate=True)
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as err:
            raise ExecutorError(422, "Only UTF-8 text files are available.") from err
        return {"content_b64": base64.b64encode(text.encode("utf-8")).decode("ascii")}

    def _write_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, _config_id, _evidence, key = self._context(payload)
        self._ensure_not_busy(key)
        with self._lock(key):
            repo, git_project_relative, _head = self._repository(project_root)
            path = payload.get("path")
            parts = self._assert_file_path(repo, git_project_relative, path)
            try:
                content = base64.b64decode(payload.get("content_b64", ""), validate=True)
            except (ValueError, TypeError) as err:
                raise ExecutorError(422, "File content must be valid base64 text.") from err
            if len(content) > MAX_FILE_BYTES:
                raise ExecutorError(413, "Files are limited to 1 MiB.")
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as err:
                raise ExecutorError(422, "File content must be UTF-8 text.") from err
            relative_path = "/".join(parts)
            self._record_owned_path(payload, project_root, repo, git_project_relative, relative_path,
                                    hashlib.sha256(content).hexdigest())
            result = self._file_worker(project_root, {
                "operation": "write", "workspace": str(self.workspace_root),
                "project_root": str(project_root), "path": relative_path,
                "content_b64": base64.b64encode(content).decode("ascii"),
            })
            return {"path": relative_path, "bytes": len(content), **result}

    def _delete_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, _config_id, _evidence, key = self._context(payload)
        self._ensure_not_busy(key)
        with self._lock(key):
            repo, git_project_relative, _head = self._repository(project_root)
            path = payload.get("path")
            parts = self._assert_file_path(repo, git_project_relative, path)
            relative_path = "/".join(parts)
            self._record_owned_path(payload, project_root, repo, git_project_relative, relative_path, None)
            result = self._file_worker(project_root, {
                "operation": "delete", "workspace": str(self.workspace_root),
                "project_root": str(project_root), "path": relative_path,
            })
            return {"path": relative_path, "deleted": True, **result}

    def _list_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, _config_id, _evidence, _key = self._context(payload)
        repository = self._optional_repository(project_root)
        repo, git_project_relative = repository if repository else (None, "")
        path = payload.get("path", ".")
        parts = self._parts(path, allow_dot=True)
        result = self._file_worker(project_root, {
            "operation": "list", "workspace": str(self.workspace_root),
            "project_root": str(project_root), "path": path,
        })
        results = []
        for item in result["items"]:
            try:
                self._parts("/".join(parts + (item["name"],)))
            except ExecutorError:
                continue
            rel = "/".join(parts + (item["name"],))
            if self._ignored(repo, git_project_relative, rel, project_root):
                continue
            results.append(rel + ("/" if item["directory"] else ""))
        if len(results) > MAX_LIST_FILES:
            raise ExecutorError(413, "This folder has more than 500 visible entries. List a smaller folder.")
        return {"files": sorted(results)}

    def _tree_state(self, repo: Path, tree: str, project_relative: str, paths: list[str]) -> dict[str, tuple[str, str, str]]:
        entries = self._tree_entries(repo, tree, project_relative)
        return {path: entries[path] for path in paths if path in entries}

    def _point_status(self, project_root: Path, project_relative: str, checkout: str, config_id: str,
                      point: dict[str, Any]) -> tuple[Path, str, str, str, str]:
        repo, repo_project_relative, before_ref, after_ref = self._point_repo(
            project_root, project_relative, point, checkout, config_id,
        )
        if not point.get("after_tree"):
            raise ExecutorError(409, "The run has no completed restore point yet.")
        expires_at = datetime.fromisoformat(str(point["expires_at"]).replace("Z", "+00:00"))
        if _now() >= expires_at:
            raise ExecutorError(410, "This restore point has expired.")
        for ref in (before_ref, after_ref):
            result = self._run_as_executor_user(
                ["git", "-C", str(repo), "show-ref", "--verify", "--quiet", ref],
                cwd=repo, env=self._safe_env(repo), timeout=20,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if result.returncode != 0:
                raise ExecutorError(410, "Git recovery data is no longer available.")
        before_tree = self._git(repo, ["rev-parse", "--verify", f"{before_ref}^{{tree}}"]).decode().strip()
        after_tree_from_ref = self._git(repo, ["rev-parse", "--verify", f"{after_ref}^{{tree}}"]).decode().strip()
        if before_tree != point.get("before_tree") or after_tree_from_ref != point.get("after_tree"):
            raise ExecutorError(409, "Git recovery data changed after it was saved.")
        return repo, repo_project_relative, before_ref, after_ref, str(point["after_tree"])

    def _restore_preview(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, config_id, _evidence, key = self._context(payload)
        self._ensure_not_busy(key)
        with self._lock(key):
            point = payload.get("point")
            repo, project_relative, before_ref, after_ref, after_tree = self._point_status(
                project_root, _relative, str(payload["checkout_path"]), config_id, point,
            )
            changes = self._changed_paths(repo, str(point["before_tree"]), after_tree, project_relative)
            before = self._tree_state(repo, str(point["before_tree"]), project_relative, changes)
            after = self._tree_state(repo, after_tree, project_relative, changes)
            head = self._git(repo, ["rev-parse", "--verify", "HEAD"]).decode().strip()
            current_tree, index = self._tree_from_worktree(repo, head, project_relative)
            index.unlink(missing_ok=True)
            current = self._tree_state(repo, current_tree, project_relative, changes)
            conflicts = []
            for rel in changes:
                try:
                    self._parts(rel)
                    if self._ignored(repo, project_relative, rel):
                        conflicts.append(rel)
                        continue
                except ExecutorError:
                    conflicts.append(rel)
                    continue
                if any(entry and entry[0] == "120000" for entry in (before.get(rel), after.get(rel), current.get(rel))):
                    conflicts.append(rel)
                    continue
                if current.get(rel) != after.get(rel):
                    conflicts.append(rel)
                    continue
                try:
                    self._reject_symlink_components(project_root, project_root / Path(rel).parent)
                    last = project_root / rel
                    if last.is_symlink():
                        conflicts.append(rel)
                except ExecutorError:
                    conflicts.append(rel)
            return {
                "run_id": point["run_id"], "changes": changes, "conflicts": sorted(set(conflicts)),
                "ready": not conflicts, "before_ref": before_ref, "after_ref": after_ref,
            }

    def _blob(self, repo: Path, entry: tuple[str, str, str]) -> bytes:
        _mode, kind, oid = entry
        if kind != "blob":
            raise ExecutorError(409, "Restore point contains an unsupported Git object.")
        size = int(self._git(repo, ["cat-file", "-s", oid]).decode().strip())
        if size > MAX_SNAPSHOT_FILE_BYTES:
            raise ExecutorError(413, "Restore data exceeds the 64 MiB per-file limit.")
        return self._git(repo, ["cat-file", "blob", oid], timeout=60)

    def _restore(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, config_id, _evidence, key = self._context(payload)
        self._ensure_not_busy(key)
        with self._lock(key):
            point = payload.get("point")
            preview = self._restore_preview(payload)
            if preview["conflicts"]:
                raise ExecutorError(409, "Restore conflicts with current file changes. Review the conflict list before retrying.")
            repo, project_relative, before_ref, after_ref, after_tree = self._point_status(
                project_root, _relative, str(payload["checkout_path"]), config_id, point,
            )
            changes = preview["changes"]
            before = self._tree_state(repo, str(point["before_tree"]), project_relative, changes)
            after = self._tree_state(repo, after_tree, project_relative, changes)
            # Preflight source blobs in the supervisor; the worker checks target
            # permissions and applies every change as the selected host user.
            plans = []
            for rel in changes:
                self._parts(rel)
                old = before.get(rel)
                new = after.get(rel)
                if old and old[0] == "120000":
                    raise ExecutorError(409, "Automatic restore does not recreate symbolic links.")
                if new and new[0] == "120000":
                    raise ExecutorError(409, "Automatic restore does not remove symbolic links.")
                if old:
                    content = self._blob(repo, old)
                    plans.append({"path": rel, "content_b64": base64.b64encode(content).decode("ascii"),
                                  "mode": int(old[0], 8) & 0o777})
                else:
                    plans.append({"path": rel, "content_b64": None, "mode": 0})
            self._file_worker(project_root, {
                "operation": "restore", "workspace": str(self.workspace_root),
                "project_root": str(project_root), "files": plans,
            })
            return {"run_id": point["run_id"], "restored_files": changes, "conflicts": []}

    def _expire_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, config_id, _evidence, key = self._context(payload)
        self._ensure_not_busy(key)
        with self._lock(key):
            point = payload.get("point")
            repo, _project_relative, before_ref, after_ref = self._point_repo(
                project_root, _relative, point, str(payload["checkout_path"]), config_id,
            )
            for ref in (before_ref, after_ref):
                exists = self._run_as_executor_user(
                    ["git", "-C", str(repo), "show-ref", "--verify", "--quiet", ref],
                    cwd=repo, timeout=30, env=self._safe_env(repo),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                if exists.returncode == 1:
                    continue
                if exists.returncode != 0:
                    raise ExecutorError(409, "Could not inspect expired Git recovery data.")
                result = self._run_as_executor_user(
                    ["git", "-C", str(repo), "update-ref", "-d", ref], cwd=repo,
                    timeout=30, env=self._safe_env(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                if result.returncode != 0:
                    raise ExecutorError(409, "Could not remove expired Git recovery data.")
            with self._receipt_lock:
                self._runs.pop(str(point["run_id"]), None)
                self._persist_runs()
            return {"run_id": point["run_id"], "expired": True}

    def _index_path(self, repo: Path) -> Path:
        raw = self._git(repo, ["rev-parse", "--git-path", "index"]).decode().strip()
        path = Path(raw)
        if not path.is_absolute():
            path = repo / path
        path = Path(os.path.abspath(path))
        try:
            path.relative_to(self.workspace_root.resolve(strict=True))
        except ValueError as err:
            raise ExecutorError(409, "The Git index is outside the selected execution mount.") from err
        return path

    def _commit_verified(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, config_id, _evidence, key = self._context(payload)
        self._ensure_not_busy(key)
        with self._lock(key):
            point = payload.get("point")
            checks = payload.get("checks")
            if not isinstance(checks, list) or not checks or any(not isinstance(item, dict) or item.get("passed") is not True for item in checks):
                return {"committed": False, "reason": "Verified build or test evidence is required before commit."}
            repo, project_relative, before_ref, after_ref, after_tree = self._point_status(
                project_root, _relative, str(payload["checkout_path"]), config_id, point,
            )
            if point.get("before_dirty"):
                return {"committed": False, "reason": "Pre-run changes are present; run changes remain reviewable in the workspace."}
            if point.get("unowned_changes"):
                return {"committed": False, "reason": "Other workspace paths changed during this run; review them before committing."}
            if point.get("changed_files") is None or not point["changed_files"]:
                return {"committed": False, "reason": "This run has no file changes to commit."}
            expected_head = str(point["head_before"])
            current_head = self._git(repo, ["rev-parse", "--verify", "HEAD"]).decode().strip()
            if current_head != expected_head:
                return {"committed": False, "reason": "The Git branch changed after this run started."}
            dirty = self._status_paths(repo, current_head, project_relative)
            expected_paths = set(point["changed_files"])
            seen_paths = set()
            for item in dirty:
                raw = item[3:] if len(item) >= 4 else item
                if raw.startswith('"'):
                    try:
                        import ast
                        raw = ast.literal_eval(raw)
                    except (SyntaxError, ValueError):
                        return {"committed": False, "reason": "Git status contains an unsafe path; changes remain reviewable."}
                prefix = project_relative + "/" if project_relative else ""
                path = raw[len(prefix):] if prefix and raw.startswith(prefix) else raw
                seen_paths.add(path)
            if seen_paths != expected_paths:
                return {"committed": False, "reason": "Workspace changes no longer match this run's saved restore point."}
            index_path = self._index_path(repo)
            index_digest = self._file_worker(project_root, {
                "operation": "index_digest", "workspace": str(self.workspace_root),
                "project_root": str(project_root), "index_path": str(index_path),
            }).get("digest", "")
            if not self._runner_access(index_path.parent, os.W_OK | os.X_OK):
                return {"committed": False, "reason": "The selected user cannot update this Git index; changes remain reviewable."}
            check_staged = self._run_as_executor_user(
                ["git", "-C", str(repo), "diff", "--cached", "--quiet", current_head],
                cwd=repo, env=self._safe_env(repo), timeout=30,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if check_staged.returncode != 0:
                return {"committed": False, "reason": "The Git index contains staged changes; run changes remain reviewable."}
            current_tree, temp_index = self._tree_from_worktree(repo, current_head, project_relative)
            try:
                if current_tree != after_tree:
                    return {"committed": False, "reason": "Workspace contents changed after verification; review the current diff."}
                env = self._safe_env(repo)
                env.update({
                    "GIT_AUTHOR_NAME": "AgentBoard Assistant", "GIT_AUTHOR_EMAIL": "assistant@agentboard.local",
                    "GIT_COMMITTER_NAME": "AgentBoard Assistant", "GIT_COMMITTER_EMAIL": "assistant@agentboard.local",
                })
                result = self._run_as_executor_user(
                    ["git", "-C", str(repo), "commit-tree", current_tree, "-p", current_head],
                    cwd=repo, env=env, timeout=120,
                    input=f"AgentBoard assistant run {point['run_id']}\n".encode(),
                )
                if result.returncode != 0:
                    raise ExecutorError(409, (result.stderr or b"").decode("utf-8", "replace")[-1000:] or "Could not create the verified run commit.")
                commit = result.stdout.decode().strip()
            finally:
                temp_index.unlink(missing_ok=True)
            symbolic = self._run_as_executor_user(
                ["git", "-C", str(repo), "symbolic-ref", "-q", "HEAD"], cwd=repo,
                env=self._safe_env(repo), timeout=30,
            )
            refname = symbolic.stdout.decode().strip() if symbolic.returncode == 0 else "HEAD"
            update = self._run_as_executor_user(
                ["git", "-C", str(repo), "update-ref", refname, commit, current_head],
                cwd=repo, env=self._safe_env(repo), timeout=30,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            if update.returncode != 0:
                return {"committed": False, "reason": "The Git branch changed during commit; the run remains reviewable."}
            temp_commit_index = self._temp_index()
            try:
                self._git(repo, ["read-tree", commit], index_file=temp_commit_index)
                index_content = base64.b64encode(temp_commit_index.read_bytes()).decode("ascii")
            finally:
                temp_commit_index.unlink(missing_ok=True)
            try:
                self._file_worker(project_root, {
                    "operation": "install_index", "workspace": str(self.workspace_root),
                    "project_root": str(project_root), "index_path": str(index_path),
                    "expected_digest": index_digest, "content_b64": index_content,
                })
            except ExecutorError:
                return {"committed": True, "commit": commit,
                        "reason": "The run commit is saved, but the selected user could not refresh the Git index. Review the repository status."}
            return {"committed": True, "commit": commit, "changed_files": sorted(expected_paths)}

    def _run_check(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_root, _relative, config_id, _evidence, key = self._context(payload)
        argv = payload.get("argv")
        if not isinstance(argv, list) or not argv or len(argv) > 64 or any(not isinstance(arg, str) or "\x00" in arg or len(arg) > 4096 for arg in argv):
            raise ExecutorError(422, "Pass a command as a non-empty argument array.")
        if sum(len(arg.encode("utf-8")) for arg in argv) > 16_000:
            raise ExecutorError(413, "The command arguments exceed the size limit.")
        self._repository(project_root)
        with self._guard:
            if key in self._active_jobs:
                raise ExecutorError(409, "A workspace check is already running.")
            job_id = hashlib.sha256(f"{time.time_ns()}:{threading.get_ident()}".encode()).hexdigest()[:20]
            self._active_jobs[key] = {"job_id": job_id, "started_at": _iso(_now())}
        captured = bytearray()
        output_lock = threading.Lock()
        truncated = threading.Event()

        def drain(stream: Any) -> None:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    return
                with output_lock:
                    captured.extend(chunk)
                    if len(captured) > MAX_OUTPUT_BYTES:
                        del captured[:len(captured) - MAX_OUTPUT_BYTES]
                        truncated.set()

        proc = None
        try:
            proc = subprocess.Popen(
                argv, cwd=str(project_root), env=self._safe_env(project_root),
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                start_new_session=True, **self._identity_kwargs(),
            )
            reader = threading.Thread(target=drain, args=(proc.stdout,), daemon=True)
            reader.start()
            try:
                exit_code = proc.wait(timeout=CHECK_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=3)
                reader.join(timeout=3)
                if proc.stdout:
                    proc.stdout.close()
                raise ExecutorError(504, "The build or test command exceeded the 15 minute limit.")
            # Do not leave detached descendants running after a command reports completion.
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            time.sleep(0.1)
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            reader.join(timeout=3)
            if proc.stdout:
                proc.stdout.close()
            with output_lock:
                output = bytes(captured).decode("utf-8", "replace")
            if truncated.is_set():
                output = "[Earlier output was truncated. Showing the final 1 MiB.]\n" + output
            return {"command": argv, "exit_code": int(exit_code), "output": output, "passed": exit_code == 0,
                    "output_truncated": truncated.is_set()}
        except FileNotFoundError as err:
            raise ExecutorError(422, f"Required command is not installed: {argv[0]}") from err
        finally:
            if proc and proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            with self._guard:
                self._active_jobs.pop(key, None)

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        operation = payload.get("operation")
        if operation == "status":
            return self.status(payload.get("checkout_path", ""))
        if operation == "resolve":
            result = self.status(payload.get("checkout_path", ""))
            if result["status"] == "Ready":
                result["project_path"] = str(self._project_mapping(payload["checkout_path"])[0])
            return result
        handlers = {
            "snapshot": self._snapshot, "finish_snapshot": self._finish_snapshot,
            "restore_preview": self._restore_preview, "restore": self._restore,
            "read_file": self._read_file, "write_file": self._write_file,
            "delete_file": self._delete_file, "list_files": self._list_files,
            "run_check": self._run_check, "expire_snapshot": self._expire_snapshot,
            "commit_verified": self._commit_verified,
        }
        if operation == "is_idle":
            _project_root, _rel, _config_id, _evidence, key = self._context(payload)
            with self._guard:
                active = self._active_jobs.get(key)
            return {"active": active is not None, "idle": active is None,
                    "runs": 1 if active else 0, "job_id": active.get("job_id") if active else None}
        if operation == "operation_receipt":
            return self._operation_receipt(payload)
        handler = handlers.get(operation)
        if handler is None:
            raise ExecutorError(404, "Unknown local execution operation.")
        if operation in {"snapshot", "finish_snapshot", "write_file", "delete_file", "restore",
                         "run_check", "expire_snapshot", "commit_verified"} and payload.get("operation_id"):
            # Verify current mount and project mapping before recording the mutation attempt.
            self._context(payload)
            return self._with_receipt(operation, payload, handler)
        return handler(payload)


class _ThreadedUnixHTTPServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True


class _Handler(http.server.BaseHTTPRequestHandler):
    server_version = "AgentBoardExecutor/1"
    sys_version = ""

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _send(self, status: int, value: dict[str, Any]) -> None:
        body = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/healthz":
            self._send(404, {"detail": "Not found."})
            return
        self._send(200, {"status": "ok"})

    def do_POST(self) -> None:
        if self.path != "/v1/dispatch":
            self._send(404, {"detail": "Not found."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"detail": "Invalid request size."})
            return
        if length < 1 or length > MAX_REQUEST_BYTES:
            self._send(413, {"detail": "Request body is too large."})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("request is not an object")
            result = self.server.executor.dispatch(payload)
            self._send(200, result)
        except ExecutorError as err:
            self._send(err.status, {"detail": str(err)})
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as err:
            self._send(400, {"detail": f"Invalid request: {err}"})
        except Exception as err:
            # Keep stack traces and request contents out of the client response.
            print(f"executor internal error: {type(err).__name__}", file=sys.stderr, flush=True)
            self._send(500, {"detail": "The local execution operation failed."})


def _child_open_directory(project_root: Path, parts: tuple[str, ...]) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        current_fd = os.open(project_root, flags)
    except OSError as err:
        raise ExecutorError(409, "The project folder cannot be opened with the selected user's permissions.") from err
    try:
        for part in parts:
            next_fd = os.open(part, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except OSError as err:
        os.close(current_fd)
        raise ExecutorError(422, "A parent folder is missing or cannot be opened safely.") from err


def _child_safe_roots(payload: dict[str, Any]) -> Path:
    workspace = Path(os.environ.get("AGENTBOARD_WORKSPACE_ROOT", "")).resolve(strict=True)
    project = Path(str(payload.get("project_root", ""))).resolve(strict=True)
    try:
        project.relative_to(workspace)
    except ValueError as err:
        raise ExecutorError(422, "The file operation is outside the selected workspace.") from err
    return project


def _child_read(project_root: Path, path: str, maximum: int) -> bytes:
    parts = WorkspaceExecutor._parts(path)
    parent_fd = _child_open_directory(project_root, parts[:-1])
    try:
        fd = os.open(parts[-1], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise ExecutorError(422, "Only regular files are available to Assistant file tools.")
            if info.st_size > maximum:
                raise ExecutorError(413, "The file exceeds the allowed size limit.")
            content = bytearray()
            while len(content) <= maximum:
                chunk = os.read(fd, min(65536, maximum + 1 - len(content)))
                if not chunk:
                    break
                content.extend(chunk)
            if len(content) > maximum:
                raise ExecutorError(413, "The file exceeds the allowed size limit.")
            return bytes(content)
        finally:
            os.close(fd)
    except FileNotFoundError as err:
        raise ExecutorError(404, "File not found.") from err
    except OSError as err:
        raise ExecutorError(422, "The file cannot be read safely with the selected user's permissions.") from err
    finally:
        os.close(parent_fd)


def _child_atomic_write(project_root: Path, path: str, content: bytes, mode: int | None = None) -> None:
    parts = WorkspaceExecutor._parts(path)
    parent_fd = _child_open_directory(project_root, parts[:-1])
    temp_name = f".agentboard-file-{os.getpid()}-{time.time_ns()}"
    try:
        try:
            existing = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing and not stat.S_ISREG(existing.st_mode):
            raise ExecutorError(422, "Only regular files can be replaced.")
        if existing and existing.st_size > MAX_FILE_BYTES:
            raise ExecutorError(413, "Files larger than 1 MiB cannot be edited by the Assistant.")
        file_mode = mode if mode is not None else (stat.S_IMODE(existing.st_mode) if existing else 0o644)
        fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent_fd)
        try:
            view = memoryview(content)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fchmod(fd, file_mode & 0o777)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(temp_name, parts[-1], src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    except FileExistsError as err:
        raise ExecutorError(409, "A temporary file already exists. Retry the write.") from err
    except OSError as err:
        raise ExecutorError(422, "The file could not be written with the selected user's permissions.") from err
    finally:
        try:
            os.unlink(temp_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        os.close(parent_fd)


def _child_directory_items(project_root: Path, path: str) -> list[dict[str, Any]]:
    parts = WorkspaceExecutor._parts(path, allow_dot=True)
    directory_fd = _child_open_directory(project_root, parts)
    try:
        items = []
        for entry in os.scandir(directory_fd):
            try:
                WorkspaceExecutor._parts(entry.name)
                info = entry.stat(follow_symlinks=False)
            except (ExecutorError, OSError):
                continue
            if stat.S_ISLNK(info.st_mode):
                continue
            if stat.S_ISDIR(info.st_mode):
                is_dir = True
            elif stat.S_ISREG(info.st_mode):
                is_dir = False
            else:
                continue
            items.append({"name": entry.name, "directory": is_dir})
            if len(items) > MAX_LIST_FILES:
                raise ExecutorError(413, "This folder has more than 500 entries. List a smaller folder.")
        return items
    finally:
        os.close(directory_fd)


def _child_delete(project_root: Path, path: str) -> None:
    parts = WorkspaceExecutor._parts(path)
    parent_fd = _child_open_directory(project_root, parts[:-1])
    try:
        try:
            info = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError as err:
            raise ExecutorError(404, "File not found.") from err
        if not stat.S_ISREG(info.st_mode):
            raise ExecutorError(422, "Only regular files can be deleted.")
        if info.st_size > MAX_FILE_BYTES:
            raise ExecutorError(413, "Files larger than 1 MiB cannot be deleted by the Assistant.")
        os.unlink(parts[-1], dir_fd=parent_fd)
    except OSError as err:
        raise ExecutorError(422, "The file could not be deleted with the selected user's permissions.") from err
    finally:
        os.close(parent_fd)


def _child_restore(project_root: Path, files: list[dict[str, Any]]) -> None:
    if not isinstance(files, list) or len(files) > MAX_LIST_FILES:
        raise ExecutorError(413, "The restore request contains too many files.")
    normalized = []
    for item in files:
        if not isinstance(item, dict):
            raise ExecutorError(422, "The restore request is invalid.")
        path = str(item.get("path", ""))
        parts = WorkspaceExecutor._parts(path)
        encoded = item.get("content_b64")
        content = None if encoded is None else base64.b64decode(encoded, validate=True)
        if content is not None and len(content) > MAX_SNAPSHOT_FILE_BYTES:
            raise ExecutorError(413, "Restore data exceeds the per-file size limit.")
        mode = int(item.get("mode", 0)) & 0o777
        parent_fd = _child_open_directory(project_root, parts[:-1])
        try:
            try:
                current = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                current = None
            if current and not stat.S_ISREG(current.st_mode):
                raise ExecutorError(409, f"Restore path is not a regular file: {path}")
            # Creating and removing a probe ensures a read-only nested directory
            # is detected before any restore path is changed.
            probe = f".agentboard-restore-probe-{os.getpid()}-{time.time_ns()}"
            probe_fd = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent_fd)
            os.close(probe_fd)
            os.unlink(probe, dir_fd=parent_fd)
        except OSError as err:
            raise ExecutorError(422, f"Restore path cannot be changed with the selected user's permissions: {path}") from err
        finally:
            os.close(parent_fd)
        normalized.append((parts, path, content, mode))
    for parts, path, content, mode in normalized:
        if content is None:
            _child_delete_restore(project_root, parts)
        else:
            _child_atomic_write(project_root, path, content, mode)


def _child_delete_restore(project_root: Path, parts: tuple[str, ...]) -> None:
    parent_fd = _child_open_directory(project_root, parts[:-1])
    try:
        try:
            os.unlink(parts[-1], dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        except OSError as err:
            raise ExecutorError(422, "The restore could not remove a run-created file.") from err
    finally:
        os.close(parent_fd)


def _child_install_index(payload: dict[str, Any]) -> dict[str, Any]:
    workspace = Path(os.environ.get("AGENTBOARD_WORKSPACE_ROOT", "")).resolve(strict=True)
    index_path = Path(os.path.abspath(str(payload.get("index_path", ""))))
    try:
        relative = index_path.relative_to(workspace)
    except ValueError as err:
        raise ExecutorError(422, "The Git index is outside the selected workspace.") from err
    parent_fd = _child_open_directory(workspace, relative.parts[:-1])
    try:
        index_name = relative.parts[-1]
        try:
            fd = os.open(index_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        except FileNotFoundError:
            fd = None
        if fd is not None:
            try:
                current = hashlib.sha256()
                while True:
                    chunk = os.read(fd, 65536)
                    if not chunk:
                        break
                    current.update(chunk)
                current_digest = current.hexdigest()
            finally:
                os.close(fd)
        else:
            current_digest = ""
        if current_digest != payload.get("expected_digest"):
            raise ExecutorError(409, "The Git index changed during commit.")
        lock_name = index_name + ".lock"
        lock_fd = os.open(lock_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=parent_fd)
        try:
            if payload.get("content_b64"):
                content = base64.b64decode(payload["content_b64"], validate=True)
            else:
                content = b""
            if len(content) > 32 * 1024 * 1024:
                raise ExecutorError(413, "The Git index exceeds the supported size limit.")
            view = memoryview(content)
            while view:
                written = os.write(lock_fd, view)
                view = view[written:]
            os.fsync(lock_fd)
        finally:
            os.close(lock_fd)
        # Recheck while holding the Git lock, then atomically install the index.
        try:
            fd = os.open(index_name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        except FileNotFoundError:
            fd = None
        if fd is not None:
            try:
                current = hashlib.sha256()
                while chunk := os.read(fd, 65536):
                    current.update(chunk)
                locked_digest = current.hexdigest()
            finally:
                os.close(fd)
        else:
            locked_digest = ""
        if locked_digest != payload.get("expected_digest"):
            raise ExecutorError(409, "The Git index changed during commit.")
        os.replace(lock_name, index_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        return {"installed": True}
    finally:
        try:
            os.unlink(relative.parts[-1] + ".lock", dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        os.close(parent_fd)


def _child_index_digest(payload: dict[str, Any]) -> dict[str, Any]:
    workspace = Path(os.environ.get("AGENTBOARD_WORKSPACE_ROOT", "")).resolve(strict=True)
    index_path = Path(os.path.abspath(str(payload.get("index_path", ""))))
    try:
        relative = index_path.relative_to(workspace)
    except ValueError as err:
        raise ExecutorError(422, "The Git index is outside the selected workspace.") from err
    parent_fd = _child_open_directory(workspace, relative.parts[:-1])
    try:
        try:
            fd = os.open(relative.parts[-1], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
        except FileNotFoundError:
            return {"digest": ""}
        try:
            digest = hashlib.sha256()
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                digest.update(chunk)
            return {"digest": digest.hexdigest()}
        finally:
            os.close(fd)
    finally:
        os.close(parent_fd)


def _run_file_operation() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ExecutorError(400, "Invalid file operation.")
        operation = payload.get("operation")
        if operation == "install_index":
            result = _child_install_index(payload)
        elif operation == "index_digest":
            result = _child_index_digest(payload)
        else:
            project_root = _child_safe_roots(payload)
            path = payload.get("path", "")
            if operation == "read":
                content = _child_read(project_root, path, MAX_FILE_BYTES)
                result = {"content_b64": base64.b64encode(content).decode("ascii")}
            elif operation == "digest":
                try:
                    content = _child_read(project_root, path, MAX_SNAPSHOT_FILE_BYTES)
                    result = {"digest": hashlib.sha256(content).hexdigest()}
                except ExecutorError as err:
                    if err.status == 404:
                        result = {"digest": None}
                    else:
                        result = {"digest": "unsupported"}
            elif operation == "write":
                content = base64.b64decode(payload.get("content_b64", ""), validate=True)
                if len(content) > MAX_FILE_BYTES:
                    raise ExecutorError(413, "Files are limited to 1 MiB.")
                try:
                    content.decode("utf-8")
                except UnicodeDecodeError as err:
                    raise ExecutorError(422, "File content must be UTF-8 text.") from err
                _child_atomic_write(project_root, path, content)
                result = {"written": True}
            elif operation == "delete":
                _child_delete(project_root, path)
                result = {"deleted": True}
            elif operation == "list":
                result = {"items": _child_directory_items(project_root, path)}
            elif operation == "restore":
                _child_restore(project_root, payload.get("files", []))
                result = {"restored": True}
            else:
                raise ExecutorError(404, "Unknown file operation.")
        sys.stdout.write(json.dumps(result, separators=(",", ":")))
    except ExecutorError as err:
        sys.stdout.write(json.dumps({"status": err.status, "detail": str(err)}, separators=(",", ":")))
        raise SystemExit(2)
    except (OSError, ValueError, TypeError) as err:
        sys.stdout.write(json.dumps({"status": 422, "detail": f"The file operation failed: {type(err).__name__}"}, separators=(",", ":")))
        raise SystemExit(2)


def _serve(socket_path: Path) -> None:
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.unlink(missing_ok=True)
    server = _ThreadedUnixHTTPServer(str(socket_path), _Handler)
    server.executor = WorkspaceExecutor(socket_gid=int(os.environ.get("AGENTBOARD_EXECUTOR_SOCKET_GID", "10001")))
    os.chmod(socket_path.parent, 0o750)
    os.chown(socket_path.parent, 0, server.executor.socket_gid)
    os.chmod(socket_path, 0o660)
    os.chown(socket_path, 0, server.executor.socket_gid)
    server.serve_forever(poll_interval=0.25)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", default="/run/agentboard-executor/executor.sock")
    parser.add_argument("--healthcheck", action="store_true")
    parser.add_argument("--file-operation", action="store_true")
    args = parser.parse_args()
    if args.healthcheck:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2)
        client.connect(args.socket)
        client.sendall(b"GET /healthz HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        if b"200" not in client.recv(256):
            raise SystemExit("executor is not ready")
        return
    if args.file_operation:
        _run_file_operation()
        return
    _serve(Path(args.socket))


if __name__ == "__main__":
    main()
