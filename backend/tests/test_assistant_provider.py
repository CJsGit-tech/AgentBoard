import asyncio
import unittest
from types import SimpleNamespace

from agents import RunConfig

from app.assistant_provider import (
    CredentialStore,
    OpenAIProviderAdapter,
    ProviderError,
    SUPPORTED_MODELS,
    normalize_provider_error,
)


class FakePage:
    def __init__(self, model_ids):
        self.data = [SimpleNamespace(id=model_id) for model_id in model_ids]


class FakeClient:
    def __init__(self, model_ids=(), response_error=None, response_status="completed", response_text="OK"):
        self.models = SimpleNamespace(list=self.list_models)
        self.responses = SimpleNamespace(create=self.create_response)
        self.model_ids = model_ids
        self.response_error = response_error
        self.response_status = response_status
        self.response_text = response_text
        self.response_calls = []
        self.closed = False

    async def list_models(self):
        return FakePage(self.model_ids)

    async def create_response(self, **kwargs):
        self.response_calls.append(kwargs)
        if self.response_error is not None:
            raise self.response_error
        return SimpleNamespace(
            id="resp-test", status=self.response_status, output_text=self.response_text
        )

    async def close(self):
        self.closed = True


class FakeRunResult:
    def __init__(self, events=(), final_output="hello", items=None, wait_until_cancelled=False):
        self._events = list(events)
        self.final_output = final_output
        self._items = items or []
        self.interruptions = []
        self.is_complete = False
        self.cancelled = asyncio.Event()
        self.cancel_calls = 0
        self.stream_closed = False
        self.wait_until_cancelled = wait_until_cancelled

    async def _event_stream(self):
        if self.wait_until_cancelled:
            await self.cancelled.wait()
        for event in self._events:
            if self.cancelled.is_set():
                return
            yield event
        self.is_complete = True

    def stream_events(self):
        return self._event_stream()

    def cancel(self):
        self.cancel_calls += 1
        self.cancelled.set()
        self.is_complete = True

    def to_input_list(self):
        return self._items


class FakeRunner:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def run_streamed(self, agent, **kwargs):
        self.calls.append((agent, kwargs))
        return self.result


class CredentialStoreTests(unittest.TestCase):
    def test_session_key_is_process_only_and_status_never_returns_key(self):
        credentials = CredentialStore(environment_key="")
        self.assertEqual(credentials.status()["source"], "none")

        status = credentials.set_session_key("  sk-secret-test  ")

        self.assertTrue(status["configured"])
        self.assertEqual(status["source"], "session")
        self.assertNotIn("sk-secret-test", str(status))
        self.assertEqual(credentials.require_key(), ("sk-secret-test", "session"))
        credentials.clear_session_key()
        self.assertEqual(credentials.status()["source"], "none")
        with self.assertRaises(ProviderError) as raised:
            credentials.require_key()
        self.assertEqual(raised.exception.code, "key_unavailable")

    def test_environment_key_wins_and_cannot_be_changed_in_ui(self):
        credentials = CredentialStore(environment_key="sk-env-secret")
        self.assertEqual(credentials.require_key(), ("sk-env-secret", "environment"))
        with self.assertRaises(ProviderError) as set_error:
            credentials.set_session_key("sk-session-secret")
        self.assertEqual(set_error.exception.code, "environment_key_configured")
        self.assertNotIn("sk-env-secret", str(set_error.exception))
        credentials.clear_session_key()
        self.assertEqual(credentials.require_key(), ("sk-env-secret", "environment"))

    def test_rejects_empty_or_oversized_session_key(self):
        credentials = CredentialStore(environment_key="")
        for key in ("", "   ", "x" * 4097):
            with self.subTest(length=len(key)), self.assertRaises(ProviderError) as raised:
                credentials.set_session_key(key)
            self.assertEqual(raised.exception.code, "invalid_key")


class OpenAIProviderAdapterTests(unittest.IsolatedAsyncioTestCase):
    def adapter(self, *, client_factory, runner=None, **kwargs):
        return OpenAIProviderAdapter(
            CredentialStore(environment_key="sk-test-secret"),
            client_factory=client_factory,
            runner=runner,
            **kwargs,
        )

    async def test_model_catalog_is_supported_and_account_intersection(self):
        self.assertEqual(
            [model["id"] for model in OpenAIProviderAdapter.supported_models()],
            [model["id"] for model in SUPPORTED_MODELS],
        )
        clients = []

        def make_client(**kwargs):
            client = FakeClient(["gpt-6-luna", "text-embedding-3-small", "unknown-model"])
            clients.append((client, kwargs))
            return client

        models = await self.adapter(client_factory=make_client).list_models()

        self.assertEqual([model["id"] for model in models], ["gpt-6-luna"])
        client, options = clients[0]
        self.assertTrue(client.closed)
        self.assertEqual(options["api_key"], "sk-test-secret")
        self.assertEqual(options["max_retries"], 0)

    async def test_validate_connection_checks_account_then_probes_responses(self):
        clients = []

        def make_client(**kwargs):
            client = FakeClient(["gpt-6-luna"])
            clients.append((client, kwargs))
            return client

        adapter = self.adapter(client_factory=make_client)
        result = await adapter.validate_connection("gpt-6-luna")

        self.assertEqual(result, {"connected": True, "model": "gpt-6-luna"})
        client, options = clients[0]
        self.assertTrue(client.closed)
        self.assertEqual(options["timeout"], 15.0)
        self.assertEqual(client.response_calls[0]["model"], "gpt-6-luna")
        self.assertEqual(client.response_calls[0]["max_output_tokens"], 256)

    async def test_connection_rejects_models_outside_account(self):
        clients = []

        def make_client(**kwargs):
            client = FakeClient(["gpt-6.2-sol"])
            clients.append(client)
            return client

        with self.assertRaises(ProviderError) as raised:
            await self.adapter(client_factory=make_client).validate_connection("gpt-6-luna")
        self.assertEqual(raised.exception.code, "model_unavailable")
        self.assertTrue(clients[0].closed)
        self.assertEqual(clients[0].response_calls, [])

    async def test_connection_does_not_accept_incomplete_or_empty_response(self):
        for status, output_text in (("incomplete", ""), ("completed", "  ")):
            with self.subTest(status=status, output_text=output_text):
                clients = []

                def make_client(**kwargs):
                    client = FakeClient(
                        ["gpt-6-luna"], response_status=status, response_text=output_text
                    )
                    clients.append(client)
                    return client

                with self.assertRaises(ProviderError) as raised:
                    await self.adapter(client_factory=make_client).validate_connection("gpt-6-luna")
                self.assertEqual(raised.exception.code, "provider_unavailable")
                self.assertTrue(clients[0].closed)

    async def test_execute_uses_scoped_client_streams_events_and_returns_full_input(self):
        previous_and_current = [
            {"role": "user", "content": "prior"},
            {"role": "user", "content": "current"},
        ]
        raw_event = SimpleNamespace(
            type="raw_response_event",
            data=SimpleNamespace(type="response.output_text.delta", delta="Hello"),
        )
        result = FakeRunResult([raw_event], "Hello, world.", previous_and_current)
        runner = FakeRunner(result)
        clients = []
        models = []
        agents = []

        def make_client(**kwargs):
            client = FakeClient()
            clients.append((client, kwargs))
            return client

        def make_model(**kwargs):
            models.append(kwargs)
            return "scoped-model"

        def make_agent(**kwargs):
            agents.append(kwargs)
            return "agent"

        adapter = self.adapter(
            client_factory=make_client,
            runner=runner,
            model_factory=make_model,
            agent_factory=make_agent,
        )
        events = []

        async def on_event(event_type, payload):
            events.append((event_type, payload))

        output = await adapter.execute(
            "gpt-6-luna",
            previous_and_current,
            "Follow the task scope.",
            ["read_file tool"],
            on_event=on_event,
        )

        self.assertEqual(output, {"output_text": "Hello, world.", "items": previous_and_current})
        self.assertEqual(events, [("assistant.delta", {"text": "Hello"})])
        client, options = clients[0]
        self.assertTrue(client.closed)
        self.assertEqual(options["api_key"], "sk-test-secret")
        self.assertEqual(models, [{"model": "gpt-6-luna", "openai_client": client}])
        self.assertEqual(agents[0]["model"], "scoped-model")
        self.assertEqual(agents[0]["tools"], ["read_file tool"])
        self.assertEqual(runner.calls[0][1]["input"], previous_and_current)
        self.assertEqual(runner.calls[0][1]["max_turns"], 16)
        self.assertIsInstance(runner.calls[0][1]["run_config"], RunConfig)
        self.assertTrue(runner.calls[0][1]["run_config"].tracing_disabled)

    async def test_execute_cancels_stream_when_runtime_requests_cancellation(self):
        result = FakeRunResult(wait_until_cancelled=True)
        runner = FakeRunner(result)
        clients = []

        def make_client(**kwargs):
            client = FakeClient()
            clients.append(client)
            return client

        checks = 0

        async def wait_for_cancel():
            nonlocal checks
            checks += 1
            return checks > 1

        with self.assertRaises(ProviderError) as raised:
            await self.adapter(client_factory=make_client, runner=runner).execute(
                "gpt-6-luna", [], "instructions", [], cancel_requested=wait_for_cancel
            )

        self.assertEqual(raised.exception.code, "cancelled")
        self.assertEqual(result.cancel_calls, 1)
        self.assertTrue(clients[0].closed)

    async def test_api_errors_are_normalized_without_upstream_text(self):
        class UpstreamError(Exception):
            status_code = 429
            request_id = "req_safe-123"

        error = normalize_provider_error(UpstreamError("leaked sk-test-secret body"))
        self.assertEqual(error.code, "rate_limited")
        self.assertTrue(error.retryable)
        self.assertEqual(error.request_id, "req_safe-123")
        self.assertNotIn("sk-test-secret", str(error))
        self.assertNotIn("leaked", str(error.public()))

    async def test_timeout_error_has_safe_retryable_message(self):
        error = normalize_provider_error(TimeoutError("secret body"))
        self.assertEqual(error.code, "provider_timeout")
        self.assertTrue(error.retryable)
        self.assertNotIn("secret body", str(error))


if __name__ == "__main__":
    unittest.main()
