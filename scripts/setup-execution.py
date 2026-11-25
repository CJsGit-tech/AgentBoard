#!/usr/bin/env python3
"""Select the host folder exposed to AgentBoard's isolated executor.

This script only applies changes with --apply. The chosen folder is mounted in
full at /workspaces. Commands run from a project may read and write anywhere in
that selected folder. The executor has no network, database, provider key, or
Docker socket. Use a dedicated source folder, not your home folder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
OVERRIDE = LOCAL / "execution.compose.yaml"
METADATA = LOCAL / "execution-selection.json"
API_BASE = "http://127.0.0.1:8080"
SOCKET_GID_BASE = 41000


def config_id(host_folder: Path) -> str:
    canonical = os.path.normpath(str(host_folder))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _yaml_quote(value: str) -> str:
    if "\n" in value or "\r" in value or "\x00" in value:
        raise ValueError("The selected folder path contains an unsupported character.")
    return "'" + value.replace("'", "''") + "'"


def build_override(host_folder: Path, uid: int, gid: int, socket_gid: int, selected_config_id: str) -> str:
    folder = _yaml_quote(str(host_folder))
    return f"""services:
  api:
    group_add:
      - \"{socket_gid}\"
    environment:
      AGENTBOARD_EXECUTION_CONFIGURED: \"1\"
    volumes:
      - execution_socket:/run/agentboard-executor:ro
  executor:
    build:
      context: ./backend
      dockerfile: Executor.Dockerfile
    user: \"0:0\"
    init: true
    read_only: true
    network_mode: none
    tmpfs:
      - /tmp:rw,noexec,nosuid,nodev,size=128m
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
    security_opt:
      - no-new-privileges:true
    environment:
      AGENTBOARD_HOST_ROOT: {folder}
      AGENTBOARD_EXECUTION_UID: \"{uid}\"
      AGENTBOARD_EXECUTION_GID: \"{gid}\"
      AGENTBOARD_EXECUTOR_SOCKET_GID: \"{socket_gid}\"
      AGENTBOARD_EXECUTOR_CONFIG_ID: \"{selected_config_id}\"
      AGENTBOARD_EXECUTOR_CONFIG_ID: \"{selected_config_id}\"
    volumes:
      - type: bind
        source: {folder}
        target: /workspaces
        bind:
          create_host_path: false
      - execution_socket:/run/agentboard-executor
      - execution_state:/var/lib/agentboard-executor
    healthcheck:
      test: [\"CMD\", \"python3\", \"-m\", \"app.executor\", \"--healthcheck\"]
      interval: 3s
      timeout: 3s
      retries: 20
    restart: unless-stopped
volumes:
  execution_socket:
    name: agentboard_mvp_assistant_executor_socket_v1
  execution_state:
    name: agentboard_mvp_assistant_executor_state_v1
"""


def validate_folder(value: str) -> Path:
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_dir():
        raise ValueError("Choose an existing folder.")
    if str(path) in ("/", ""):
        raise ValueError("Choose a dedicated project folder below the filesystem root.")
    home = Path.home().resolve(strict=True)
    if home == path or home.is_relative_to(path):
        raise ValueError("Choose a source folder below your home folder, not your home folder or one of its parents.")
    if "\n" in str(path) or "\r" in str(path):
        raise ValueError("The selected folder path contains an unsupported character.")
    if os.getuid() == 0:
        raise ValueError("Run setup as your normal account, not as root.")
    return path


def _request(path: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        API_BASE + path, data=data, method=method,
        headers={"X-AgentBoard-UI": "1", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = response.read(65536)
    except urllib.error.HTTPError as err:
        detail = err.read(65536).decode("utf-8", "replace")
        raise RuntimeError(f"AgentBoard rejected local execution setup ({err.code}): {detail}") from err
    except (urllib.error.URLError, TimeoutError) as err:
        raise RuntimeError("Start AgentBoard first. Local execution setup needs the Assistant API to check active file jobs.") from err
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as err:
        raise RuntimeError("AgentBoard returned an invalid setup response.") from err
    if not isinstance(value, dict):
        raise RuntimeError("AgentBoard returned an invalid setup response.")
    return value


def wait_for_idle(timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while True:
        state = _request("/api/assistant/execution/active")
        if not state.get("active") and not int(state.get("runs", 0)):
            return
        if time.monotonic() >= deadline:
            raise RuntimeError("File jobs are still active. Setup did not restart the executor.")
        print("Waiting for active Assistant file jobs to finish before changing the mount.", flush=True)
        time.sleep(2)


def apply_configuration(host_folder: Path, selected_config_id: str, timeout: int) -> None:
    wait_for_idle(timeout)
    result = _request("/api/assistant/execution/configuration", method="POST", body={
        "host_folder": str(host_folder), "config_id": selected_config_id,
    })
    if result.get("status") not in ("Restart required", "Ready"):
        raise RuntimeError("AgentBoard did not record the requested execution folder.")


def write_atomic(path: Path, content: str) -> None:
    LOCAL.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Select the exact host folder mounted into AgentBoard's isolated Assistant executor.",
        epilog="Commands can read and write anywhere inside this selected folder. Choose a dedicated source folder, not your home folder.",
    )
    parser.add_argument("--folder", required=True, help="Existing host folder to expose at /workspaces")
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--dry-run", action="store_true", help="Show the exact folder and changes without writing or restarting")
    choice.add_argument("--apply", action="store_true", help="Save the selected folder and restart the isolated executor")
    parser.add_argument("--wait-seconds", type=int, default=600, help="Maximum time to wait for active file jobs")
    args = parser.parse_args()
    try:
        host_folder = validate_folder(args.folder)
        selected_config_id = config_id(host_folder)
        uid, gid = os.getuid(), os.getgid()
        if args.wait_seconds < 0 or args.wait_seconds > 3600:
            raise ValueError("Wait time must be between 0 and 3600 seconds.")
        socket_gid = SOCKET_GID_BASE + (gid % 1000)
        if socket_gid == gid or socket_gid == uid:
            socket_gid += 1
        override = build_override(host_folder, uid, gid, socket_gid, selected_config_id)
        metadata = json.dumps({"host_folder": str(host_folder), "config_id": selected_config_id}, indent=2) + "\n"
        if args.dry_run:
            print(f"Selected host folder: {host_folder}")
            print(f"Executor mount: {host_folder} -> /workspaces")
            print(f"Would write ignored setup metadata: {OVERRIDE.relative_to(ROOT)} and {METADATA.relative_to(ROOT)}")
            print("Would rebuild only the API and isolated executor after active file jobs finish.")
            return 0
        apply_configuration(host_folder, selected_config_id, args.wait_seconds)
        write_atomic(OVERRIDE, override)
        write_atomic(METADATA, metadata)
        command = [
            "docker", "compose", "-f", "compose.yaml", "-f", str(OVERRIDE.relative_to(ROOT)),
            "up", "--build", "-d", "--wait", "api", "executor",
        ]
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Docker Compose exited with status {result.returncode}. The selected folder is saved; rerun this command to apply it.")
        print(f"Local execution is configured for {host_folder}.")
        return 0
    except (OSError, ValueError, RuntimeError) as err:
        print(f"setup-execution: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
