"""Provider SDK boundary for isolated, text-only AgentBoard runs."""

import os
import tempfile
from collections.abc import Callable, Mapping
from typing import Any, Protocol


class AgentAdapter(Protocol):
    async def run(self, prompt: str, *, activity: Callable[[str, str], None],
                  model: str | None = None) -> dict[str, Any]: ...


_PROVIDER_ENV = {
    "codex": ("OPENAI_API_KEY",),
    "claude": ("ANTHROPIC_API_KEY",),
}
_SENSITIVE_ENV = (
    "DATABASE_URL",
    "AGENTBOARD_BROWSER_TOKEN_FILE",
    "AGENTBOARD_MCP_TOKEN_FILE",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
)


def _provider_environment(provider: str, source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Copy only provider credentials; never load dotenv files or ambient settings."""
    source = os.environ if source is None else source
    # SDK subprocess environments inherit their parent. Blank known application
    # secrets first, then restore only this provider's explicitly allowed key.
    env = {name: "" for name in _SENSITIVE_ENV}
    env.update({name: source[name] for name in _PROVIDER_ENV[provider] if source.get(name)})
    return env


class CodexSDKAdapter:
    async def run(self, prompt: str, *, activity: Callable[[str, str], None],
                  model: str | None = None) -> dict[str, Any]:
        try:
            from openai_codex import ApprovalMode, AsyncCodex, CodexConfig, Sandbox
        except ImportError as exc:
            raise RuntimeError("openai-codex package is not installed") from exc

        # Keep the run independent from user/project Codex config and MCP servers.
        # Login writes auth state only inside this run-scoped, disposable home.
        with tempfile.TemporaryDirectory(prefix="agentboard-codex-") as codex_home:
            provider_env = _provider_environment("codex")
            provider_env["CODEX_HOME"] = codex_home
            config = CodexConfig(
                cwd="/tmp",
                env=provider_env,
                config_overrides=(
                    "features.shell_tool=false",
                    "features.unified_exec=false",
                    'web_search="disabled"',
                    "mcp_servers={}",
                ),
            )
            async with AsyncCodex(config=config) as codex:
                await codex.login_api_key(provider_env["OPENAI_API_KEY"])
                thread = await codex.thread_start(
                    model=model or os.environ.get("AGENTBOARD_CODEX_MODEL"),
                    cwd="/tmp",
                    ephemeral=True,
                    sandbox=Sandbox.read_only,
                    approval_mode=ApprovalMode.deny_all,
                    base_instructions=(
                        "Respond to the user's prompt as text only. Do not use tools, "
                        "access files, run commands, or contact external services."
                    ),
                )
                result = await thread.run(
                    prompt,
                    model=model or os.environ.get("AGENTBOARD_CODEX_MODEL"),
                    sandbox=Sandbox.read_only,
                    approval_mode=ApprovalMode.deny_all,
                )
        response = result.final_response or ""
        activity("provider_message", response[:1000])
        return {"text": response}


class ClaudeAgentSDKAdapter:
    async def run(self, prompt: str, *, activity: Callable[[str, str], None],
                  model: str | None = None) -> dict[str, Any]:
        try:
            from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query
        except ImportError as exc:
            raise RuntimeError("claude-agent-sdk package is not installed") from exc

        output: list[str] = []
        options = ClaudeAgentOptions(
            model=model or os.environ.get("AGENTBOARD_CLAUDE_MODEL"),
            cwd="/tmp",
            tools=[],
            allowed_tools=[],
            mcp_servers={},
            setting_sources=[],
            plugins=[],
            skills=[],
            permission_mode="dontAsk",
            env=_provider_environment("claude"),
            max_turns=1,
        )
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        output.append(block.text)
                        activity("provider_message", block.text[:1000])
            elif isinstance(message, ResultMessage) and message.result:
                # Preserve the SDK's final text if an SDK version emits it separately.
                if not output:
                    output.append(message.result)
        return {"text": "".join(output)}


def adapter_for(provider: str) -> AgentAdapter:
    if provider == "codex":
        return CodexSDKAdapter()
    if provider == "claude":
        return ClaudeAgentSDKAdapter()
    raise ValueError("Unsupported provider")
