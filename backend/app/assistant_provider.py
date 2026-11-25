"""OpenAI credentials and Agents SDK adapter for the in-app assistant.

Credentials stay in this process. This module does not read browser storage,
write credentials to disk, or use the Agents SDK's process-global client.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import re
from collections.abc import AsyncIterable, Iterable, Mapping
from typing import Any, Callable

from agents import Agent, AsyncOpenAI, OpenAIResponsesModel, RunConfig, Runner, ModelSettings
from agents.exceptions import MaxTurnsExceeded
from openai import APIConnectionError, APIError, APITimeoutError


MAX_TURNS = 16
REQUEST_TIMEOUT_SECONDS = 60.0
CONNECTION_TIMEOUT_SECONDS = 15.0
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


# These models are the small, supported Responses API catalog. Account access
# is checked separately with the authenticated Models endpoint.
SUPPORTED_MODELS: tuple[dict[str, str], ...] = (
    {"id": "gpt-6.2-astra", "name": "GPT-6.2 Astra"},
    {"id": "gpt-6.2-sol", "name": "GPT-6.2 Sol"},
    {"id": "gpt-6.1-terra", "name": "GPT-6.1 Terra"},
    {"id": "gpt-6-luna", "name": "GPT-6 Luna"},
    {"id": "gpt-5.2", "name": "GPT-5.2"},
    {"id": "gpt-5.1", "name": "GPT-5.1 (deprecated)"},
    {"id": "gpt-5-mini", "name": "GPT-5 mini (deprecated)"},
)
_MODEL_BY_ID = {model["id"]: model for model in SUPPORTED_MODELS}


class ProviderError(Exception):
    """A stable, safe error shape for API handlers and run records."""

    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.request_id = request_id

    def public(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.request_id:
            result["request_id"] = self.request_id
        return result


class CredentialStore:
    """Environment-first credentials with a process-memory BYOK fallback."""

    def __init__(self, environment_key: str | None = None) -> None:
        # None means read once at process startup. Supplying an explicit value
        # lets tests distinguish an empty environment from the real process.
        self._environment_key = (
            os.environ.get("OPENAI_API_KEY") if environment_key is None else environment_key
        )
        self._session_key: str | None = None

    def status(self) -> dict[str, Any]:
        source = self._source()
        if source == "environment":
            notice = "Change the local environment key and restart AgentBoard to replace it."
        elif source == "session":
            notice = "This key stays in backend memory and is cleared when AgentBoard restarts."
        else:
            notice = "Add an OpenAI API key to connect the assistant."
        return {
            "configured": source != "none",
            "source": source,
            "notice": notice,
        }

    def set_session_key(self, key: str) -> dict[str, Any]:
        if self._environment_key:
            raise ProviderError(
                "environment_key_configured",
                "The environment key is managed outside the Assistant settings.",
            )
        if not isinstance(key, str) or not key.strip() or len(key) > 4096:
            raise ProviderError("invalid_key", "Enter a valid OpenAI API key.")
        self._session_key = key.strip()
        return self.status()

    def clear_session_key(self) -> dict[str, Any]:
        self._session_key = None
        return self.status()

    def require_key(self) -> tuple[str, str]:
        source = self._source()
        if source == "environment":
            return self._environment_key or "", source
        if source == "session":
            return self._session_key or "", source
        raise ProviderError("key_unavailable", "Add an OpenAI API key before connecting.")

    def _source(self) -> str:
        if self._environment_key:
            return "environment"
        if self._session_key:
            return "session"
        return "none"


class OpenAIProviderAdapter:
    """Minimal run-scoped adapter backed by OpenAI Agents SDK 0.25."""

    provider_id = "openai"

    def __init__(
        self,
        credentials: CredentialStore,
        *,
        client_factory: Callable[..., Any] | None = None,
        model_factory: Callable[..., Any] | None = None,
        agent_factory: Callable[..., Any] | None = None,
        runner: Any | None = None,
    ) -> None:
        self.credentials = credentials
        self._client_factory = client_factory or AsyncOpenAI
        self._model_factory = model_factory or OpenAIResponsesModel
        self._agent_factory = agent_factory or Agent
        self._runner = runner or Runner

    @staticmethod
    def supported_models() -> list[dict[str, str]]:
        """Static catalog for the UI when no key or network is available."""
        return [dict(model) for model in SUPPORTED_MODELS]

    @staticmethod
    def capabilities(model_id: str) -> dict[str, bool]:
        if model_id not in _MODEL_BY_ID:
            raise ProviderError("model_unavailable", "Choose a supported OpenAI model.")
        return {
            "text": True,
            "streaming": True,
            "local_function_tools": True,
            "approval_interruptions": True,
            "structured_output": True,
            "agent_as_tool_delegation": True,
        }

    async def list_models(self) -> list[dict[str, str]]:
        """Return supported models present in the configured account catalog."""
        key, _source = self.credentials.require_key()
        client = self._new_client(key)
        try:
            account_ids = await self._account_model_ids(client)
            return [model for model in self.supported_models() if model["id"] in account_ids]
        except ProviderError:
            raise
        except Exception as error:
            raise normalize_provider_error(error) from None
        finally:
            await _close_client(client)

    async def validate_connection(self, model_id: str) -> dict[str, Any]:
        self._require_supported_model(model_id)
        key, _source = self.credentials.require_key()
        client = self._new_client(key, timeout=CONNECTION_TIMEOUT_SECONDS)
        try:
            account_ids = await self._account_model_ids(client)
            if model_id not in account_ids:
                raise ProviderError(
                    "model_unavailable",
                    "This model is not available to the configured OpenAI account.",
                )
            response = await client.responses.create(
                model=model_id,
                input="Reply with OK.",
                max_output_tokens=256,
            )
            output_text = getattr(response, "output_text", None)
            if getattr(response, "status", None) != "completed" or not (
                isinstance(output_text, str) and output_text.strip()
            ):
                raise ProviderError(
                    "provider_unavailable",
                    "OpenAI did not return a completed response. Try the connection check again.",
                    True,
                    _safe_request_id(getattr(response, "_request_id", None)),
                )
            return {"connected": True, "model": model_id}
        except ProviderError:
            raise
        except Exception as error:
            raise normalize_provider_error(error) from None
        finally:
            await _close_client(client)

    async def execute(
        self,
        model_id: str,
        input_items: list[Any],
        instructions: str,
        tools: list[Any],
        on_event: Callable[[str, dict[str, Any]], Any] | None = None,
        cancel_requested: Callable[[], Any] | asyncio.Event | None = None,
    ) -> dict[str, Any]:
        """Run one streamed, bounded agent turn and return its complete input list."""
        self._require_supported_model(model_id)
        if cancel_requested is not None and await _is_cancel_requested(cancel_requested):
            raise _cancelled_error()
        key, _source = self.credentials.require_key()
        client = self._new_client(key)
        try:
            model = self._model_factory(model=model_id, openai_client=client)
            agent = self._agent_factory(
                name="AgentBoard Assistant",
                instructions=instructions,
                model=model,
                tools=list(tools),
                model_settings=ModelSettings(parallel_tool_calls=False),
            )
            result = self._runner.run_streamed(
                agent,
                input=input_items,
                max_turns=MAX_TURNS,
                run_config=RunConfig(tracing_disabled=True),
            )
            stream = result.stream_events()
            cancelled = asyncio.Event()
            watcher = asyncio.create_task(
                _watch_for_cancellation(cancel_requested, result, cancelled)
            )
            try:
                async for event in stream:
                    if cancelled.is_set():
                        break
                    await _forward_event(event, on_event)
                if cancelled.is_set():
                    raise _cancelled_error()
            except BaseException:
                if not cancelled.is_set() and not getattr(result, "is_complete", True):
                    result.cancel()
                raise
            finally:
                watcher.cancel()
                await _await_cancelled_task(watcher)
                # The watcher already requested immediate cancellation. Close
                # the iterator after the SDK has stopped its run task.
                await _close_stream(stream)

            interruptions = getattr(result, "interruptions", None)
            if interruptions:
                raise ProviderError(
                    "uncertain",
                    "The run paused for approval and needs review before it can continue.",
                )
            if not getattr(result, "is_complete", False):
                raise ProviderError(
                    "uncertain",
                    "The run stopped before completion. Review its saved state before continuing.",
                )
            output_text = getattr(result, "final_output", None)
            if output_text is None:
                output_text = ""
            elif not isinstance(output_text, str):
                output_text = str(output_text)
            return {"output_text": output_text, "items": result.to_input_list()}
        except ProviderError:
            raise
        except Exception as error:
            raise normalize_provider_error(error) from None
        finally:
            await _close_client(client)

    def _new_client(self, key: str, *, timeout: float = REQUEST_TIMEOUT_SECONDS) -> Any:
        try:
            return self._client_factory(api_key=key, timeout=timeout, max_retries=0)
        except Exception as error:
            raise normalize_provider_error(error) from None

    @staticmethod
    def _require_supported_model(model_id: str) -> None:
        if model_id not in _MODEL_BY_ID:
            raise ProviderError("model_unavailable", "Choose a supported OpenAI model.")

    @staticmethod
    async def _account_model_ids(client: Any) -> set[str]:
        page = await client.models.list()
        account_ids: set[str] = set()
        if hasattr(page, "__aiter__"):
            async for item in page:
                model_id = _read_model_id(item)
                if model_id:
                    account_ids.add(model_id)
        else:
            rows = getattr(page, "data", page)
            if isinstance(rows, Iterable):
                for item in rows:
                    model_id = _read_model_id(item)
                    if model_id:
                        account_ids.add(model_id)
        return account_ids


async def _watch_for_cancellation(
    requested: Callable[[], Any] | asyncio.Event | None,
    result: Any,
    cancelled: asyncio.Event,
) -> None:
    if requested is None:
        return
    while True:
        if await _is_cancel_requested(requested):
            cancelled.set()
            result.cancel()
            return
        await asyncio.sleep(0.1)


async def _is_cancel_requested(requested: Callable[[], Any] | asyncio.Event) -> bool:
    if isinstance(requested, asyncio.Event):
        return requested.is_set()
    value = requested()
    if inspect.isawaitable(value):
        value = await value
    return bool(value)


async def _forward_event(
    event: Any,
    on_event: Callable[[str, dict[str, Any]], Any] | None,
) -> None:
    if on_event is None:
        return
    event_type: str | None = None
    payload: dict[str, Any] = {}
    event_kind = getattr(event, "type", None)
    data = getattr(event, "data", None)
    if event_kind == "raw_response_event":
        delta = getattr(data, "delta", None)
        data_type = getattr(data, "type", None)
        if isinstance(delta, str) and (data_type is None or data_type == "response.output_text.delta"):
            event_type = "assistant.delta"
            payload = {"text": delta}
    elif event_kind == "run_item_stream_event":
        name = getattr(event, "name", None)
        if name == "tool_called":
            event_type = "tool.started"
            tool_name = _tool_name(getattr(event, "item", None))
            if tool_name:
                payload = {"name": tool_name}
        elif name == "tool_output":
            event_type = "tool.finished"
            tool_name = _tool_name(getattr(event, "item", None))
            if tool_name:
                payload = {"name": tool_name}
    if event_type is None:
        return
    value = on_event(event_type, payload)
    if inspect.isawaitable(value):
        await value


def _tool_name(item: Any) -> str | None:
    raw_item = getattr(item, "raw_item", None)
    name = getattr(raw_item, "name", None)
    if isinstance(name, str) and 0 < len(name) <= 120:
        return name
    return None


def _read_model_id(item: Any) -> str | None:
    model_id = item.get("id") if isinstance(item, Mapping) else getattr(item, "id", None)
    return model_id if isinstance(model_id, str) else None


async def _close_client(client: Any) -> None:
    close = getattr(client, "close", None)
    if close is None:
        return
    try:
        value = close()
        if inspect.isawaitable(value):
            await value
    except Exception as error:
        raise normalize_provider_error(error) from None


async def _close_stream(stream: Any) -> None:
    close = getattr(stream, "aclose", None)
    if close is not None:
        value = close()
        if inspect.isawaitable(value):
            await value


async def _await_cancelled_task(task: asyncio.Task[Any]) -> None:
    try:
        await task
    except asyncio.CancelledError:
        return


def normalize_provider_error(error: BaseException) -> ProviderError:
    """Map upstream failures to fixed text and non-secret metadata."""
    request_id = _safe_request_id(getattr(error, "request_id", None))
    if isinstance(error, MaxTurnsExceeded):
        return ProviderError("step_limit", "The task reached its step limit. Review the saved progress before continuing.", False, request_id)
    if isinstance(error, APITimeoutError) or isinstance(error, (TimeoutError, asyncio.TimeoutError)):
        return ProviderError("provider_timeout", "OpenAI did not respond in time. Try again.", True, request_id)
    status = getattr(error, "status_code", None)
    if isinstance(status, int):
        if status in (401, 403):
            return ProviderError("invalid_key", "OpenAI rejected this API key. Check the key and try again.", False, request_id)
        if status == 429:
            return ProviderError("rate_limited", "OpenAI rate limit reached. Try again shortly.", True, request_id)
        if status == 408:
            return ProviderError("provider_timeout", "OpenAI did not respond in time. Try again.", True, request_id)
        if status in (400, 404):
            return ProviderError("model_unavailable", "This model is not available for this request.", False, request_id)
        if isinstance(status, int) and status >= 500:
            return ProviderError("provider_unavailable", "OpenAI is temporarily unavailable. Try again.", True, request_id)
    if isinstance(error, APIConnectionError):
        return ProviderError("provider_unavailable", "OpenAI could not be reached. Check the connection and try again.", True, request_id)
    if isinstance(error, APIError):
        return ProviderError("provider_unavailable", "OpenAI could not complete the request. Try again.", True, request_id)
    if "tool" in type(error).__name__.lower() and "error" in type(error).__name__.lower():
        return ProviderError("tool_failed", "A local assistant tool failed. Review the run details.", False, request_id)
    logging.getLogger(__name__).error("Agent SDK execution failed: %s",type(error).__name__)
    return ProviderError("execution_failed", "The assistant could not complete this run. Review the run status and try again.", True, request_id)


def _safe_request_id(value: Any) -> str | None:
    return value if isinstance(value, str) and _REQUEST_ID_RE.fullmatch(value) else None


def _cancelled_error() -> ProviderError:
    return ProviderError("cancelled", "The run was cancelled.", False)
