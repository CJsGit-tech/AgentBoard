# Connect Codex and Claude Code

The command guide is available offline. Setup checks the live session before changing records. AgentBoard runs locally as the React UI, API and PostgreSQL in Docker Compose. Its MCP launcher starts a standard-I/O server in the running API container. Use the shared database through MCP.

## Check the current session

1. Look for the configured native MCP server (the app README uses `agentboard-mvp`). Accept an existing alias if the user or host configuration identifies it as the intended AgentBoard instance. Discover the tools for this request and call `list_records` with `{"kind":"projects","limit":1}`. A successful empty list is a valid connection. For nonempty results, the launcher returns a record_url using the published port of the same Compose instance. Follow that origin for all links.
2. If that fails, check the intended live checkout and service. From the AgentBoard repository, `docker compose ps` shows service health. Check `http://127.0.0.1:8080/` for the default browser UI. The proxy serves only `/api/` to FastAPI. The API container has its own health check, so a page at `/healthz` on port 8080 does not prove API health.
3. Verify the host's registration with `codex mcp get agentboard-mvp` or `claude mcp get agentboard-mvp`. For Claude local scope, use the same working directory/project context as the registration. When a running chat predates registration or has a closed transport, validate in a fresh session. If the intended host lacks access to local Docker, report that restriction. A healthy stack, registration output and a direct stdio probe each answer a different question.

## Install only as requested

Install from the AgentBoard checkout using `python3 scripts/install-skill.py install --host codex --scope project` or `--host claude`. Project targets are `.agents/skills/agentbuild` for Codex and `.claude/skills/agentbuild` for Claude. Use `--project /path/to/your/project` for another checkout, or `--scope personal` for `~/.agents/skills/agentbuild` or `~/.claude/skills/agentbuild`. Existing legacy `~/.codex/skills/agentbuild` installations are not changed automatically; avoid duplicate installations.

Use the same options with `update` or `uninstall`. Updates preserve the previous managed bundle outside skill discovery. Modified or unmanaged installations are refused. Codex invocation policy ships in `agents/openai.yaml`; the installer adds Claude's explicit-only frontmatter to its generated copy. The installer does not register MCP or change credentials.

Use the actual AgentBoard README startup instructions. With the app running, register the MCP launcher from the **AgentBoard checkout**, even when the tracked project's code lives somewhere else. These are host setup commands, entered only for the client the user wants to configure.

```sh
codex mcp add agentboard-mvp -- "$PWD/scripts/agentboard-mcp" Codex
claude mcp add --scope local --transport stdio agentboard-mvp -- "$PWD/scripts/agentboard-mcp" Claude
```

Claude Code local scope is per project directory. To register the same launcher for a session launched from a different code repository, run the registration from that directory and give it the absolute path to the AgentBoard launcher. A user-scope registration is a separate choice when the user wants it across projects. The process must be able to run Docker locally. This launcher is for local hosts. Cloud access requires a supported transport and deployment of its own.

Open a fresh session. Setup starts with a real project read. Use the [record model](records.md) for writes. If native MCP is unavailable, report which checks succeeded and suggest the specific repair. Verify live operations from native MCP tool results.

For app setup, open the README from the configured AgentBoard checkout. For host behavior, use the [Claude Code skill guide](https://code.claude.com/docs/en/skills) and [MCP guide](https://code.claude.com/docs/en/mcp).
