"""Exercise the mounted FastMCP transport through FastAPI authentication."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from starlette.testclient import TestClient
from app.api.errors import ApiError
from app.main import app
from app.settings import settings


class FastMCPTransportTests(unittest.TestCase):
    def test_authenticated_discovery_and_tool_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            token = "test-token-" + "x" * 40
            path = Path(directory) / "tokens.json"
            path.write_text(json.dumps({token: {"client_id": str(uuid4()), "name": "test"}}))
            with patch("app.main.SessionLocal"), patch.object(settings, "mcp_token_file", str(path)), TestClient(app, base_url="http://127.0.0.1:8080") as client:
                headers = {"Authorization": "Bearer " + token, "Accept": "application/json, text/event-stream"}
                init = client.post("/mcp/", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}}})
                self.assertEqual(init.status_code, 200)
                headers["Mcp-Session-Id"] = init.headers["mcp-session-id"]
                discovery = client.post("/mcp/", headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
                self.assertIn('"get_project"', discovery.text)
                with patch("app.mcp.operations.dispatch", new=AsyncMock(side_effect=ApiError(404, "not_found", "Project not found"))):
                    result = client.post("/mcp/", headers=headers, json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "get_project", "arguments": {"project_id": str(uuid4())}}})
                self.assertIn('"isError":true', result.text)
                self.assertIn("not_found", result.text)
                unauthorized = client.post("/mcp/", json={"jsonrpc": "2.0", "id": 4, "method": "tools/list"})
                self.assertEqual(unauthorized.status_code, 401)
