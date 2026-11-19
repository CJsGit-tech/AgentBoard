import json
import unittest
from unittest.mock import Mock

import httpx

from app.sdk.adapters import AnthropicMessagesAdapter, OpenAIResponsesAdapter, ProviderRequestError


class ApiAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_responses_tool_loop(self):
        requests = []
        replies = [
            {"output": [{"type": "function_call", "name": "get_project", "call_id": "c1", "arguments": "{}"}]},
            {"output": [{"type": "message", "content": [{"type": "output_text", "text": "Read."}]}]},
        ]

        async def handler(request):
            requests.append(request)
            return httpx.Response(200, json=replies.pop(0))

        execute_tool = Mock(return_value={"id": "project"})
        adapter = OpenAIResponsesAdapter("secret", transport=httpx.MockTransport(handler))
        result = await adapter.run("inspect", model="test-model", history=[], execute_tool=execute_tool, activity=Mock())
        self.assertEqual(result, {"text": "Read."})
        self.assertEqual(execute_tool.call_args.args, ("get_project", {}, "c1"))
        self.assertEqual(requests[0].headers["authorization"], "Bearer secret")
        first_body = json.loads(requests[0].content)
        self.assertFalse(first_body["store"])
        self.assertEqual(first_body["model"], "test-model")
        self.assertEqual(json.loads(requests[1].content)["input"][-1]["type"], "function_call_output")

    async def test_anthropic_http_error_does_not_expose_body(self):
        async def handler(_request):
            return httpx.Response(401, json={"error": {"message": "secret token leaked"}})

        adapter = AnthropicMessagesAdapter("secret", transport=httpx.MockTransport(handler))
        with self.assertRaises(ProviderRequestError) as caught:
            await adapter.run("inspect", model="test-model", history=[], execute_tool=Mock(), activity=Mock())
        self.assertIn("HTTP 401", str(caught.exception))
        self.assertNotIn("secret", str(caught.exception))


class PlaygroundInputTests(unittest.TestCase):
    def test_empty_prompt_and_unsupported_provider_are_rejected(self):
        from pydantic import ValidationError
        from app.sdk.routes import RunCreate
        with self.assertRaises(ValidationError):
            RunCreate(provider="openai", prompt="   ")
        with self.assertRaises(ValidationError):
            RunCreate(provider="unsupported", prompt="Hello")
        body = RunCreate(provider=" OpenAI ", prompt=" Hello ", model="   ")
        self.assertEqual(body.provider, "codex")
        self.assertEqual(body.prompt, "Hello")
        self.assertIsNone(body.model)


if __name__ == "__main__":
    unittest.main()
