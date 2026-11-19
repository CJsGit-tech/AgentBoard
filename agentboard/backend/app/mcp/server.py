"""Authenticated MCP Streamable HTTP server for AgentBoard."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

from jsonschema import ValidationError
from mcp.server import ServerRequestContext
from mcp.server.request_state import RequestStateSecurity
from fastmcp import FastMCP
from fastmcp.tools import Tool as FastMCPTool, ToolResult, InputRequiredToolResult
from fastmcp.server.dependencies import get_context
from mcp.types import CallToolRequestParams, CallToolResult, TextContent

from app.api.errors import ApiError
from app.db.session import SessionLocal
from app.mcp.auth import McpBearerMiddleware, current_client, request_state_key
from app.mcp.catalog import TOOLS
from app.mcp import operations


logger = logging.getLogger(__name__)


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


class AgentBoardTool(FastMCPTool):
    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        context = get_context()
        request = context.request_context
        if request is None:
            raise RuntimeError("An authenticated MCP request is required")
        params = CallToolRequestParams(name=self.name, arguments=arguments,
                                      request_state=context.request_state,
                                      input_responses=context.input_responses)
        result = await _call_tool(request._srctx, params)
        from mcp.types import InputRequiredResult
        if isinstance(result, InputRequiredResult):
            return InputRequiredToolResult(result)
        return ToolResult(content=result.content, structured_content=result.structured_content,
                          is_error=result.is_error)


mcp_server = FastMCP("AgentBoard", request_state_security=RequestStateSecurity(
    keys=[request_state_key()], audience="AgentBoard"))
for definition in TOOLS.values():
    mcp_server.add_tool(AgentBoardTool(
        name=definition["name"], description=definition["description"],
        parameters=definition["inputSchema"], output_schema=definition["outputSchema"],
        annotations=definition["annotations"],
    ))

_transport_app = mcp_server.http_app(path="/", json_response=False,
    allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"])
asgi_app = McpBearerMiddleware(_transport_app)
