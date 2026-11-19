"""Run the AgentBoard MCP server over local stdio for Claude Desktop."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import quote


def _bootstrap_compose_environment() -> None:
    """Recreate the private runtime environment normally prepared by the image entrypoint."""
    if not os.environ.get("DATABASE_URL"):
        password_file = Path("/run/secrets/db_password")
        if not password_file.is_file():
            raise RuntimeError("Run this entrypoint inside the AgentBoard Compose backend")
        password = quote(password_file.read_text(encoding="utf-8").strip(), safe="")
        os.environ["DATABASE_URL"] = f"postgresql+psycopg://agentboard:{password}@db:5432/agentboard"
    if not os.environ.get("AGENTBOARD_MCP_TOKEN_FILE"):
        token_file = Path("/run/secrets/mcp_token")
        if not token_file.is_file():
            raise RuntimeError("The mounted MCP client credential map is unavailable")
        os.environ["AGENTBOARD_MCP_TOKEN_FILE"] = str(token_file)


def _claude_desktop_identity():
    from app.mcp.auth import _credentials

    matches = {
        client.id: client
        for client in _credentials().values()
        if client.name == "Claude Desktop"
    }
    if len(matches) != 1:
        raise RuntimeError("Configure exactly one Claude Desktop identity in the MCP credential map")
    return next(iter(matches.values()))


async def _run() -> None:
    from mcp.server.stdio import stdio_server

    from app.mcp.auth import current_client
    from app.mcp.server import mcp_server

    identity = _claude_desktop_identity()
    identity_token = current_client.set(identity)
    try:
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )
    finally:
        current_client.reset(identity_token)


def main() -> None:
    try:
        _bootstrap_compose_environment()
        asyncio.run(_run())
    except Exception as exc:
        print(f"AgentBoard MCP stdio startup failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
