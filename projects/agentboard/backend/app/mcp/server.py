"""Authenticated MCP Streamable HTTP server for AgentBoard."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from jsonschema import ValidationError
from mcp.server import Server, ServerRequestContext
from mcp.server.request_state import RequestStateBoundary, RequestStateSecurity
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolRequestParams, CallToolResult, ListToolsResult, PaginatedRequestParams, TextContent, Tool, ToolAnnotations
from starlette.applications import Starlette

from app.api.errors import ApiError
from app.db.session import SessionLocal
from app.mcp.auth import McpBearerMiddleware, current_client, request_state_key
from app.mcp.catalog import TOOLS
from app.mcp import operations


logger = logging.getLogger(__name__)


def _tool_objects() -> list[Tool]:
    result: list[Tool] = []
    for definition in TOOLS.values():
        hint = definition["annotations"]
        result.append(Tool(
            name=definition["name"], description=definition["description"],
            input_schema=definition["inputSchema"], output_schema=definition["outputSchema"],
            annotations=ToolAnnotations(
                read_only_hint=hint.get("readOnlyHint", False),
                destructive_hint=hint.get("destructiveHint", False),
                open_world_hint=hint.get("openWorldHint", False),
            ),
        ))
    return result


TOOLS_FOR_DISCOVERY = _tool_objects()


async def _list_tools(_ctx: ServerRequestContext, _params: PaginatedRequestParams | None) -> ListToolsResult:
    return ListToolsResult(tools=TOOLS_FOR_DISCOVERY)


def _error_payload(error: ApiError) -> dict:
    return {"outcome": "error", "applied": False,
            "error": {"code": error.code, "message": error.message, "fields": error.fields or {}},
            "request_id": str(uuid4())}


def _validation_payload(error: ValidationError) -> dict:
    field = ".".join(str(part) for part in error.absolute_path) or "body"
    return {"outcome": "error", "applied": False,
            "error": {"code": "invalid_input", "message": f"Invalid {field}: {error.message}", "fields": {field: error.message}},
            "request_id": str(uuid4())}


def _call_result(value: dict, *, is_error: bool = False) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(value, ensure_ascii=False, default=str))],
        structured_content=value,
        is_error=is_error,
    )


async def _call_tool(ctx: ServerRequestContext, params: CallToolRequestParams) -> CallToolResult | Any:
    definition = TOOLS.get(params.name)
    if definition is None:
        return _call_result({"outcome": "error", "applied": False,
            "error": {"code": "unknown_tool", "message": "Unknown AgentBoard tool", "fields": {}},
            "request_id": str(uuid4())}, is_error=True)
    arguments = params.arguments or {}
    try:
        definition["input_validator"].validate(arguments)
    except ValidationError as exc:
        return _call_result(_validation_payload(exc), is_error=True)
    client = current_client.get()
    if client is None:
        return _call_result({"outcome": "error", "applied": False,
            "error": {"code": "unauthorized", "message": "Authenticated MCP client is unavailable", "fields": {}},
            "request_id": str(uuid4())}, is_error=True)

    response_token = operations.input_round.set((params.request_state, params.input_responses))
    db = SessionLocal()
    try:
        value = await operations.dispatch(ctx, db, params.name, arguments, client)
        from mcp.types import InputRequiredResult
        if isinstance(value, InputRequiredResult):
            return value
        definition["output_validator"].validate(value)
        is_error = value.get("outcome") in {"error", "rejected", "cancelled", "expired"}
        return _call_result(value, is_error=is_error)
    except ApiError as exc:
        db.rollback()
        payload = _error_payload(exc)
        return _call_result(payload, is_error=True)
    except ValidationError as exc:
        db.rollback()
        return _call_result(_validation_payload(exc), is_error=True)
    except Exception:
        db.rollback()
        logger.exception("AgentBoard MCP tool failed: %s", params.name)
        payload = {"outcome": "error", "applied": False,
                   "error": {"code": "internal_error", "message": "The operation could not be completed", "fields": {}},
                   "request_id": str(uuid4())}
        return _call_result(payload, is_error=True)
    finally:
        db.close()
        operations.input_round.reset(response_token)


mcp_server = Server("AgentBoard", on_list_tools=_list_tools, on_call_tool=_call_tool)
mcp_server.middleware.append(RequestStateBoundary(
    RequestStateSecurity(keys=[request_state_key()], audience="AgentBoard"),
    default_audience="AgentBoard",
))

_transport_app = mcp_server.streamable_http_app(
    # SSE responses keep the request channel open for legacy client elicitation.
    # Newer clients can use InputRequiredResult on the same Streamable HTTP endpoint.
    streamable_http_path="/", json_response=False,
    host="127.0.0.1",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
    ),
)
asgi_app = McpBearerMiddleware(_transport_app)
session_manager = mcp_server.session_manager

