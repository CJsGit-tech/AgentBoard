# AgentBoard

AgentBoard runs on your personal computer. The desktop browser and configured MCP clients share projects, agent roles, tickets, documents, and activity stored in Postgres.

## Run with Docker Compose

From this folder, with Docker running:

```sh
python3 infra/init-secrets.py
docker compose up --build -d --wait
```

Open [AgentBoard](http://127.0.0.1:8080). The local workspace opens directly. Browser requests use automatic CSRF protection. The database and FastAPI listen on the internal Compose network. Postgres data lives in the `agentboard_pgdata` volume. `docker compose down` stops the service and preserves that volume.

### Playground

Open the Playground tab, enable workspace runs, and select OpenAI or Anthropic. Choose a model, enter a prompt, and optionally select a ticket or document as context. Continue a conversation with Reply, inspect tool activity, and cancel active runs. Proposed updates and deletions require an explicit browser approval tied to the exact changes and record revision.

Configure provider credentials in the local `.env` file before starting Compose. OpenAI reads `OPENAI_API_KEY` and `OPENAI_DEFAULT_MODEL`. Anthropic reads `ANTHROPIC_API_KEY` or `CLAUDE_API_KEY`, and `CLAUDE_DEFAULT_MODEL`. Explicit `AGENTBOARD_CODEX_MODEL` and `AGENTBOARD_CLAUDE_MODEL` values override the defaults. Credentials remain in the backend runtime. The playground uses provider HTTP APIs.

The packaged FastAPI application serves the React build, REST endpoints, live events, and the mounted FastMCP server on the same address. For development, run the backend on port 8000 and `npm run dev` in `frontend/`; Vite proxies application requests to the backend. Set `VITE_AGENTBOARD_MODE=connected` and `AGENTBOARD_ORIGIN=http://localhost:4203` for a connected development session.

See the [architecture](docs/technical-architecture/README.md) and [engineering backlog](docs/tickets/README.md) for implementation context.

## Back up the database

Run `sh infra/backup.sh` from the project folder to save a Postgres archive in `.local/backups`. The script checks the archive can be listed and prunes its archives after 30 days. To run it daily, schedule it through your operating system. Before relying on an archive, restore it to a separate database and check document and ticket reads. Keep the credential files in `.local` separately.

## AgentBuild

Connect clients to `http://127.0.0.1:8080/mcp`. The local `.local/mcp_token` JSON file maps bearer tokens to named client identities. Put each client's **own** token in its environment and keep the token out of saved config and source control.

Codex configuration:

```toml
[mcp_servers.agentboard]
url = "http://127.0.0.1:8080/mcp"
bearer_token_env_var = "AGENTBOARD_CODEX_TOKEN"
```

Claude Code configuration:

```json
{
  "mcpServers": {
    "agentboard": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": { "Authorization": "Bearer ${AGENTBOARD_CLAUDE_TOKEN}" }
    }
  }
}
```

Claude Desktop runs a local MCP server process. Run `command -v docker` in a terminal and use the returned absolute path, since graphical apps can start with a different search path. Replace the Compose file path with the absolute path on your computer as well.

```json
{
  "mcpServers": {
    "agentboard": {
      "command": "/absolute/path/to/docker",
      "args": [
        "compose",
        "-f",
        "/absolute/path/to/AgentBoard/agentboard/compose.yaml",
        "exec",
        "-T",
        "backend",
        "agentboard-entrypoint",
        "python",
        "-m",
        "app.mcp.stdio"
      ]
    }
  }
}
```

This starts the local stdio bridge in the running Compose backend and uses the configured **Claude Desktop** identity from `.local/mcp_token`. It requires access to this computer's Docker daemon and a running AgentBoard stack. It does not expose AgentBoard to the internet. Keep the config local and do not add a bearer token; the bridge loads the mounted credential map.

A verified connection writes directly to the matching AgentBoard project. An agent can create and read records. Its updates and deletions require approval through a client that supports the request. A pending ticket shows **Needs approval** alongside its normal status.

Default MCP credentials can submit pending requests. Enable interactive approval for a credential only after confirming that its exact client setup presents the proposed change and waits for a person to accept or decline. Use a dedicated credential for that setup and keep it out of headless or automatic execution. See the [approval flow](docs/technical-architecture/approval-flow.md) for the credential field and verification requirements.

After editing the credential map, run `docker compose up -d --no-deps --force-recreate --wait backend` to reload the mounted file and close stdio sessions using the previous copy. Reconnect clients after the health check passes.

AgentBuild automatic startup remains deferred. Existing file-only projects remain independent.
