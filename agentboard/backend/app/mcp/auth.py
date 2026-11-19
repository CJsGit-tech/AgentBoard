"""Bearer credential validation for the local MCP endpoint."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
import hmac
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from starlette.responses import JSONResponse

from app.settings import settings


@dataclass(frozen=True)
class McpClient:
    id: UUID
    name: str
    interactive_approval_verified: bool = False


current_client: ContextVar[McpClient | None] = ContextVar("agentboard_mcp_client", default=None)


def _credentials() -> dict[str, McpClient]:
    path = settings.mcp_token_file
    if not path:
        return {}
    try:
        raw: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict) or not raw:
        return {}
    credentials: dict[str, McpClient] = {}
    for token, value in raw.items():
        if not isinstance(token, str) or len(token) < 32 or not isinstance(value, dict):
            continue
        try:
            client_id = UUID(value["client_id"])
            name = value["name"]
        except (KeyError, TypeError, ValueError):
            continue
        if not isinstance(name, str) or not name.strip() or len(name) > 128:
            continue
        credentials[token] = McpClient(
            client_id, name.strip(), value.get("interactive_approval_verified") is True,
        )
    return credentials


def request_state_key() -> bytes:
    """Stable key for sealed multi-round-trip approval state on this installation."""
    path = settings.mcp_token_file
    if not path:
        return hashlib.sha256(b"agentboard-mcp-unconfigured").digest()
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raw = b"agentboard-mcp-unconfigured"
    return hashlib.sha256(b"agentboard-mcp-request-state\0" + raw).digest()


def authenticate(authorization: str | None) -> McpClient | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    supplied = authorization[7:].strip()
    if not supplied:
        return None
    match: McpClient | None = None
    for token, client in _credentials().items():
        if hmac.compare_digest(supplied, token):
            match = client
    return match


class McpBearerMiddleware:
    """Reject unauthenticated transport calls and bind verified identity per task."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        client = authenticate(headers.get("authorization"))
        if client is None:
            response = JSONResponse(
                {"error": "unauthorized", "message": "A valid AgentBoard MCP bearer credential is required"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return
        token = current_client.set(client)
        try:
            await self.app(scope, receive, send)
        finally:
            current_client.reset(token)
