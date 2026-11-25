"""API-side client for the isolated Assistant workspace executor.

The Path carried by WorkspaceHandle is a display/locking key only. The API
container does not mount or dereference the selected host workspace.
"""

from __future__ import annotations

import http.client
import json
import os
import socket
import shlex
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from .store import Problem


SOCKET_PATH = Path(os.environ.get("AGENTBOARD_EXECUTOR_SOCKET", "/run/agentboard-executor/executor.sock"))
_RPC_TIMEOUT_SECONDS = 960


@dataclass(frozen=True)
class WorkspaceHandle:
    """Opaque mapping token returned after the executor verifies a project."""

    path: Path
    checkout_path: str
    config_id: str
    operation_id: str | None = None
    run_id: str | None = None

    def __str__(self) -> str:
        return str(self.path)


class _UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path: Path, timeout: int) -> None:
        super().__init__("localhost", timeout=timeout)
        self._socket_path = socket_path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(str(self._socket_path))
        self.sock = sock


def _rpc(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    connection = _UnixHTTPConnection(SOCKET_PATH, _RPC_TIMEOUT_SECONDS)
    try:
        body = json.dumps({"operation": operation, **payload}, separators=(",", ":")).encode("utf-8")
        connection.request("POST", "/v1/dispatch", body=body,
                           headers={"Content-Type": "application/json", "Content-Length": str(len(body))})
        response = connection.getresponse()
        raw = response.read(2_200_000)
        try:
            data = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            raise Problem(503, "The local execution service returned an invalid response.") from err
        if not isinstance(data, dict):
            raise Problem(503, "The local execution service returned an invalid response.")
        if response.status >= 400:
            raise Problem(int(response.status), str(data.get("detail", "The local execution request failed.")))
        return data
    except Problem:
        raise
    except (OSError, http.client.HTTPException, TimeoutError) as err:
        raise Problem(503, "Local execution is unavailable. Start or restart AgentBoard after setup.") from err
    finally:
        connection.close()


def execution_status(project: dict[str, Any]) -> dict[str, Any]:
    checkout_path = str(project.get("checkout_path", ""))
    if not checkout_path:
        return {
            "status": "Not configured", "host_folder": "", "container_folder": "/workspaces",
            "project_path": "", "access": "read/write",
            "message": "Set a project checkout folder and choose a local execution folder.",
            "setup_command": "python scripts/setup-execution.py --folder <folder> --dry-run",
        }
    try:
        result = _rpc("status", {"checkout_path": checkout_path})
    except Problem as err:
        if err.status == 503:
            configured = os.environ.get("AGENTBOARD_EXECUTION_CONFIGURED") == "1"
            return {
                "status": "Unavailable" if configured else "Not configured",
                "host_folder": "", "container_folder": "/workspaces",
                "project_path": "", "access": "read/write",
                "message": str(err) if configured else "Choose a host folder and set up local execution.",
                "setup_command": "python3 scripts/setup-execution.py --folder <folder> --dry-run",
            }
        raise
    folder = str(result.get("host_folder", ""))
    if folder:
        result["setup_command"] = f"python3 scripts/setup-execution.py --folder {shlex.quote(folder)} --apply"
    else:
        result.setdefault("setup_command", "python3 scripts/setup-execution.py --folder <folder> --dry-run")
    return result


def require_workspace(project: dict[str, Any]) -> WorkspaceHandle:
    checkout_path = str(project.get("checkout_path", ""))
    if not checkout_path:
        raise Problem(409, "Choose a project checkout folder and set up local execution first.")
    result = _rpc("resolve", {"checkout_path": checkout_path})
    if result.get("status") != "Ready" or not result.get("project_path") or not result.get("config_id"):
        status = result.get("status", "Unavailable")
        message = result.get("message", "Local execution is not ready for this project.")
        raise Problem(409 if status in ("Not configured", "Restart required") else 503, message)
    return WorkspaceHandle(Path(str(result["project_path"])), checkout_path, str(result["config_id"]))


def _handle(root: WorkspaceHandle | Path) -> WorkspaceHandle:
    if isinstance(root, WorkspaceHandle):
        return root
    # A bare path is accepted for callers that retain handles within one API
    # process. The remote service still validates the mapping on every call.
    raise Problem(422, "Use the workspace handle returned by require_workspace().")


def _context(root: WorkspaceHandle | Path) -> dict[str, str]:
    handle = _handle(root)
    context = {"checkout_path": handle.checkout_path, "config_id": handle.config_id}
    if handle.operation_id:
        context["operation_id"] = handle.operation_id
    if handle.run_id:
        context["run_id"] = handle.run_id
    return context


def snapshot(root: WorkspaceHandle | Path, run_id: str) -> dict[str, Any]:
    return _rpc("snapshot", {**_context(root), "run_id": run_id})


def finish_snapshot(root: WorkspaceHandle | Path, point: dict[str, Any]) -> dict[str, Any]:
    return _rpc("finish_snapshot", {**_context(root), "point": point})


def restore_preview(root: WorkspaceHandle | Path, point: dict[str, Any]) -> dict[str, Any]:
    return _rpc("restore_preview", {**_context(root), "point": point})


def restore(root: WorkspaceHandle | Path, point: dict[str, Any]) -> dict[str, Any]:
    return _rpc("restore", {**_context(root), "point": point})


def read_file(root: WorkspaceHandle | Path, path: str) -> str:
    result = _rpc("read_file", {**_context(root), "path": path})
    import base64

    return base64.b64decode(result["content_b64"], validate=True).decode("utf-8")


def write_file(root: WorkspaceHandle | Path, path: str, content: str) -> dict[str, Any]:
    import base64

    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return _rpc("write_file", {**_context(root), "path": path, "content_b64": encoded})


def delete_file(root: WorkspaceHandle | Path, path: str) -> dict[str, Any]:
    return _rpc("delete_file", {**_context(root), "path": path})


def list_files(root: WorkspaceHandle | Path, path: str = ".") -> list[str]:
    result = _rpc("list_files", {**_context(root), "path": path})
    return list(result["files"])


def run_check(root: WorkspaceHandle | Path, argv: Sequence[str]) -> dict[str, Any]:
    return _rpc("run_check", {**_context(root), "argv": list(argv)})


def is_idle(root: WorkspaceHandle | Path) -> dict[str, Any]:
    """Return the executor's active-job state for Continue/Restore gating."""
    return _rpc("is_idle", _context(root))


def operation_receipt(root: WorkspaceHandle | Path, operation_id: str) -> dict[str, Any]:
    """Read the executor's durable record without replaying the operation."""
    context = _context(root)
    context.pop("operation_id", None)
    return _rpc("operation_receipt", {**context, "operation_id": operation_id})


def cleanup_expired(
    root: WorkspaceHandle | Path, points: Iterable[dict[str, Any]], now: datetime | None = None,
) -> list[str]:
    current = now or datetime.now(timezone.utc)
    removed: list[str] = []
    for point in points:
        expires_at = datetime.fromisoformat(str(point["expires_at"]).replace("Z", "+00:00"))
        if current >= expires_at:
            _rpc("expire_snapshot", {**_context(root), "point": point})
            removed.append(str(point.get("run_id", "")))
    return removed


def commit_verified(
    root: WorkspaceHandle | Path, point: dict[str, Any], checks: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a run-only commit when the pre-run state was completely clean."""
    return _rpc("commit_verified", {
        **_context(root), "point": point, "checks": list(checks or []),
    })
