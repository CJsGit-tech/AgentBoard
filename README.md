# AgentBoard

AgentBoard is a local workspace for people and AI agents. It stores projects, roles, tickets, documents, revisions, and activity in PostgreSQL. A React app, FastAPI API, and MCP server share the same records.

The supported deployment is a single-machine Docker Compose installation. The web service binds to `127.0.0.1:8080`; it is not configured as a public internet service. Do not expose it directly to the internet. A public deployment needs a reviewed TLS, network access, authentication, and operational design.

## Features

- Manage projects, agent roles, tickets, and documents.
- Track activity and document revisions.
- Connect MCP clients to read and create records.
- Require explicit client approval for supported agent updates and deletions.
- Optionally run workspace conversations with OpenAI or Anthropic providers.

## Requirements

- macOS, Windows, or Linux
- Docker Desktop or Docker Engine with Docker Compose v2
- Git, to clone and update the repository
- For local code development: Python 3.12 and Node.js 22 with npm
- Optional: an OpenAI or Anthropic API key for Playground runs

## Quick start

1. Clone the repository and open its root folder:

   ```sh
   git clone <repository-url>
   cd AgentBoard
   ```

2. Create the local secret files. This command is safe to rerun; it keeps existing credentials:

   ```sh
   python3 infra/init-secrets.py
   ```

   It creates `.local/db_password` and `.local/mcp_token` with restricted file permissions. These files are ignored by Git and mounted into the relevant containers at runtime.

3. Optional: configure provider keys. Copy the example file, then edit `.env`:

   ```sh
   cp -n .env.example .env
   ```

   Provider keys are only needed for Playground runs. Never commit `.env` or put provider keys in frontend variables.

4. Build and start the services:

   ```sh
   docker compose up --build -d --wait
   ```

5. Open [http://127.0.0.1:8080](http://127.0.0.1:8080). Confirm the app is healthy:

   ```sh
   docker compose ps
   curl --fail http://127.0.0.1:8080/healthz
   ```

Compose starts PostgreSQL, applies database migrations, then starts the API/web app and hourly activity cleanup. It waits for health checks before returning.

## Configuration

Set optional values in `.env` before starting or recreating the backend:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Enables OpenAI Playground runs. |
| `ANTHROPIC_API_KEY` | Enables Anthropic Playground runs. `CLAUDE_API_KEY` is also accepted. |
| `OPENAI_DEFAULT_MODEL` | Default OpenAI model. `AGENTBOARD_CODEX_MODEL` overrides it. |
| `CLAUDE_DEFAULT_MODEL` | Default Anthropic model. `AGENTBOARD_CLAUDE_MODEL` overrides it. |
| `AGENTBOARD_CODEX_SDK_ENABLED` | Enables the OpenAI workspace adapter when set to `true`. |
| `AGENTBOARD_CLAUDE_AGENT_SDK_ENABLED` | Enables the Anthropic workspace adapter when set to `true`. |

After changing values, recreate the backend so it receives the new environment:

```sh
docker compose up -d --no-deps --force-recreate --wait backend
```

The provider credentials stay in the backend container environment. The browser never receives them.

## MCP clients

The MCP endpoint is `http://127.0.0.1:8080/mcp`. Tokens are stored in `.local/mcp_token`, one per configured client identity. Keep each token private and pass it through that client's environment variable or secret store.

Example Codex configuration:

```toml
[mcp_servers.agentboard]
url = "http://127.0.0.1:8080/mcp"
bearer_token_env_var = "AGENTBOARD_CODEX_TOKEN"
```

Claude Code example:

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

For Claude Desktop, use the stdio bridge in `backend/app/mcp/stdio.py`. Point its `command` to the absolute path from `command -v docker`, then pass `compose -f /absolute/path/to/AgentBoard/compose.yaml exec -T backend agentboard-entrypoint python -m app.mcp.stdio` as its arguments. The bridge reads the `Claude Desktop` identity from `.local/mcp_token`; see [AgentBuild integration](docs/technical-architecture/agentbuild-integration.md) for behavior and security boundaries.

AgentBoard allows clients to create and read records. Updates and deletions require an approval-capable client to show the exact proposed change and wait for a person to accept or decline. Do not enable interactive approval for unattended clients.

## Operations

```sh
# View service state
docker compose ps

# Follow service logs
docker compose logs -f backend

# Stop services; keep the database volume
docker compose down

# Start again
docker compose up -d --wait

# Create and validate a PostgreSQL backup in .local/backups
sh infra/backup.sh
```

The database lives in the named Docker volume `agentboard_pgdata`. `docker compose down` preserves it. **`docker compose down -v` deletes the database volume and its data.** Store backups and `.local` credentials separately from the repository checkout. Before relying on backups, restore one to a separate database and verify important records.

For a fresh checkout that should use an existing database volume, keep the Compose project name `agentboard` and the volume name `agentboard_pgdata` unchanged.

## Local development

Docker Compose is the recommended way to run the complete app. For frontend or backend work, use the Compose PostgreSQL service and run the app processes on the host.

Start PostgreSQL and install the app dependencies:

```sh
python3 infra/init-secrets.py
docker compose up -d db
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend
npm ci
```

Open a second terminal at the repository root. Activate the same environment, then start the backend on port `8000` and apply migrations:

```sh
source .venv/bin/activate
export DATABASE_URL="postgresql+psycopg://agentboard:$(cat .local/db_password)@127.0.0.1:5432/agentboard"
export AGENTBOARD_ORIGIN="http://127.0.0.1:4203"
export AGENTBOARD_MCP_TOKEN_FILE="../.local/mcp_token"
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In the first terminal, start Vite from `frontend/`:

```sh
VITE_AGENTBOARD_MODE=connected npm run dev
```

Open [http://127.0.0.1:4203](http://127.0.0.1:4203). Vite proxies API, MCP, event, and health requests to the backend.

## Checks

Run the backend unit tests and frontend checks before submitting changes:

```sh
source .venv/bin/activate
cd backend
python -m unittest discover -s tests
cd ../frontend
npm ci
npm run typecheck
npm run build
```

The browser UI suite uses Playwright and a local Chrome installation. Start the local development backend and run `npm run test:ui` from `frontend/` to execute it.

## Repository map

```text
backend/       FastAPI app, MCP server, migrations, and backend tests
frontend/      React app, Vite config, and browser tests
infra/         Docker image, secret initialization, and backup scripts
docs/          Product, design, API, security, and operations documentation
agents/        Agent role prompts used by the project
agentboard-skill/  Separate reusable AgentBoard project skill
compose.yaml   Local multi-service deployment
```

Start with [docs/README.md](docs/README.md) for product and technical documentation. The [security guide](docs/technical-architecture/security.md) describes trust boundaries and approval behavior.
