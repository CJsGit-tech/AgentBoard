# Deployment and Operations

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Define the proposed local runtime, startup order and recovery process.

## Deployment & Operations

| Service | Responsibility / access |
| --- | --- |
| `web` | Vite static build + reverse proxy; only published port: `127.0.0.1:8080` |
| `backend` | FastAPI REST/MCP/SSE and shared services; internal `8000` |
| `db` | Postgres; internal `5432`; volume `agentboard_pgdata` |
| `migrate` | One-shot Alembic job after database health |
| `maintenance` | Backend image, database access, no listener; expiry/cleanup; no Redis/queue required |

```text
db healthy → migrations succeed → backend + maintenance → ready web proxy
```

- Readiness requires healthchecks/dependency conditions, not merely container startup.
- Unready backend produces an explicit unavailable state.
- Proxy `/api/`, `/mcp` and `/events` to FastAPI with streaming preserved and buffering disabled. Browser navigation falls back to the SPA; unknown API paths return JSON errors rather than HTML.
- Pin tested images/dependencies; keep stable Compose project/volume names.
- Build Vite assets in a Node stage; production web serves static files.
- Run migrations once, never concurrently in workers. Clean/filter expired data before serving.
- Maintenance takes a database lock to prevent duplicate cleanup.
- Secrets use restricted local config or mounted secret files—not Git or frontend build variables.

## Recovery — Proposed

| Stage | Action |
| --- | --- |
| Backup | Daily local `pg_dump` archive outside the volume; retain no longer than 30 days |
| Configuration | Preserve matching roles/setup separately without exposing secrets |
| Restore | Fresh volume → apply expiry/history limits → verify document reads and ticket counts → switch |
| Rollback | Matching pre-upgrade database backup; never assume old images read new schemas |

A consistent dump is not a tested backup until restoration succeeds. Historical backups may contain pruned revisions until backup expiry; live history remains bounded. Stricter physical-erasure requirements need clarification before implementation.

## Boundaries

- `compose down` preserves named volumes; removing the database volume destroys live data.
- Build-time internet access is separate from runtime provider access.
- No containers or client integrations have been configured by these documents.

[History rules](document-history.md) · [Log retention](activity-logging.md) · [Trust boundaries](security.md)
