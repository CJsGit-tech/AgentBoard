"""Prepare a disposable Compose instance and private desktop MCP settings.

This helper never launches a desktop client. It holds the fixture open until
the operator presses Enter or interrupts it, then removes its exact Compose
project, named volume, and private configuration directory.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = PROJECT_ROOT / "compose.yaml"


def _write_private(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(value)


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _compose_args(docker: str, project: str, override: Path) -> list[str]:
    return [
        docker, "compose", "--project-name", project,
        "--project-directory", str(PROJECT_ROOT),
        "-f", str(COMPOSE_FILE), "-f", str(override),
    ]


def _save_recovery(directory: Path, compose: list[str], volume: str, project: str) -> Path:
    recovery = directory / "RECOVERY.txt"
    commands = [
        "Disposable AgentBoard cleanup did not finish. The credentials and override remain in this private directory.",
        f"Project: {project}",
        f"Volume: {volume}",
        "Run these commands after Docker is available:",
        shlex.join([*compose, "down", "--volumes", "--remove-orphans"]),
        shlex.join(["rm", "-r", str(directory)]),
    ]
    _write_private(recovery, "\n".join(commands) + "\n")
    return recovery


def _run_captured(command: list[str], log_path: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        _write_private(log_path, "STDOUT\n" + result.stdout + "\nSTDERR\n" + result.stderr)
    return result


def _prepare(directory: Path, project: str, volume: str, docker: str, port: int,
             pending_only: bool) -> tuple[Path, Path, Path]:
    directory.chmod(0o700)
    secret_dir = directory / "secrets"
    secret_dir.mkdir(mode=0o700)
    credentials_path = secret_dir / "mcp_token"
    codex_token = secrets.token_urlsafe(36)
    claude_token = secrets.token_urlsafe(36)
    verification = not pending_only
    identities = {
        codex_token: {
            "client_id": str(uuid4()),
            "name": "Codex desktop",
            "interactive_approval_verified": verification,
        },
        claude_token: {
            "client_id": str(uuid4()),
            "name": "Claude Desktop",
            "interactive_approval_verified": verification,
        },
    }
    _write_private(secret_dir / "db_password", secrets.token_urlsafe(36) + "\n")
    _write_private(credentials_path, json.dumps(identities, indent=2) + "\n")

    override = directory / "compose.override.json"
    override_data = {
        "services": {
            "backend": {"ports": [f"127.0.0.1:{port}:8000"]},
        },
        "volumes": {"pgdata": {"name": volume}},
        "secrets": {
            "db_password": {"file": str(secret_dir / "db_password")},
            "mcp_token": {"file": str(credentials_path)},
        },
    }
    _write_private(override, json.dumps(override_data, indent=2) + "\n")

    codex_dir = directory / "codex-profile"
    codex_dir.mkdir(mode=0o700)
    codex_settings = (
        "[mcp_servers.agentboard_verification]\n"
        f'url = "http://127.0.0.1:{port}/mcp/"\n'
        f'http_headers = {{ Authorization = {json.dumps("Bearer " + codex_token)} }}\n'
    )
    _write_private(codex_dir / "config.toml", codex_settings)

    compose = _compose_args(docker, project, override)
    stdio_command = [
        *compose, "exec", "-T", "backend", "agentboard-entrypoint", "python", "-m", "app.mcp.stdio",
    ]
    claude_config = {
        "mcpServers": {
            "agentboard-verification": {
                "command": docker,
                "args": stdio_command[1:],
            }
        }
    }
    claude_path = directory / "claude_desktop_config.json"
    _write_private(claude_path, json.dumps(claude_config, indent=2) + "\n")
    return override, claude_path, codex_dir / "config.toml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an isolated AgentBoard desktop-verification fixture.")
    parser.add_argument("--port", type=int, default=18081, help="loopback HTTP port for the disposable backend (default: 18081)")
    parser.add_argument("--pending-only", action="store_true", help="mark both synthetic MCP identities as not interactively approval-verified")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if not COMPOSE_FILE.is_file():
        print(f"Compose file not found: {COMPOSE_FILE}", file=sys.stderr)
        return 2
    docker = shutil.which("docker")
    if not docker:
        print("Docker CLI was not found on PATH.", file=sys.stderr)
        return 2
    docker = str(Path(docker).resolve())
    if not _port_available(args.port):
        print(f"Could not bind 127.0.0.1:{args.port}. Choose a free loopback port with --port.", file=sys.stderr)
        return 2

    unique = uuid4().hex
    project = f"agentboard-desktop-verify-{unique[:12]}"
    volume = f"agentboard_desktop_verify_{unique}_pgdata"
    directory = Path(tempfile.mkdtemp(prefix=f"{project}-"))
    os.chmod(directory, 0o700)
    started = False
    cleanup_failed = False
    compose: list[str] = []
    try:
        override, claude_path, codex_path = _prepare(
            directory, project, volume, docker, args.port, args.pending_only,
        )
        compose = _compose_args(docker, project, override)
        up = _run_captured([*compose, "up", "--no-build", "--wait", "backend"], directory / "compose-start.log")
        if up.returncode:
            errors = up.stderr.strip().splitlines()
            reason = errors[-1].strip() if errors else f"exit {up.returncode}"
            print(f"Disposable Compose startup failed. {reason}", file=sys.stderr)
            return 1
        started = True
        mode = "pending-only" if args.pending_only else "interactive-approval-capable synthetic clients"
        print(f"Disposable AgentBoard is ready at http://127.0.0.1:{args.port} ({mode}).")
        print(f"Codex profile settings: {codex_path}")
        print(f"Claude Desktop config: {claude_path}")
        print("Use these settings in your signed-in test profiles and keep the generated files private.")
        try:
            input("Press Enter or Ctrl-C to stop and remove this fixture. ")
        except (KeyboardInterrupt, EOFError):
            pass
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"Fixture preparation failed ({type(exc).__name__}).", file=sys.stderr)
        return 1
    finally:
        if compose:
            down = _run_captured(
                [*compose, "down", "--volumes", "--remove-orphans"],
                directory / "compose-cleanup.log",
            )
        else:
            down = subprocess.CompletedProcess([], 0)
        cleanup_failed = down.returncode != 0
        if cleanup_failed:
            recovery = _save_recovery(directory, compose, volume, project)
            print(f"Cleanup did not finish. Recovery details and credentials remain at {recovery}", file=sys.stderr)
            if down.returncode:
                print(f"Compose cleanup log: {directory / 'compose-cleanup.log'}", file=sys.stderr)
        else:
            try:
                shutil.rmtree(directory)
            except OSError:
                cleanup_failed = True
                print(f"The fixture stopped, but could not remove its private directory at {directory}.", file=sys.stderr)
    return 0 if started and not cleanup_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
