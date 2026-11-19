---
name: "Deployment and Operations"
description: "Define the proposed local runtime, startup order and recovery process."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:reliability", "concern:privacy", "concern:data-integrity", "concern:security"]
---

# Deployment and Operations

> Owner: Solution Architect | Version: 0.1.4 | Status: draft | Last Updated: 2026-11-18

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

## First-run path and future automation

- Docker Compose is the first supported install and run path. The user starts the documented Compose application and confirms the web app and MCP endpoint are ready.
- AgentBuild connected mode writes directly to verified AgentBoard records once the user has an available, healthy app connection. It does not create a parallel local project copy.
- Automatic AgentBuild launch, readiness probing, and app keep-alive behavior are deferred. No supported launcher, health-check interface, or lifecycle integration has been selected; the skill must not guess a Compose project or start arbitrary containers.
- If AgentBoard is not available, AgentBuild follows its established choice between explicit file-only mode and cancel; it does not silently change storage mode.
- AgentBuild does not launch or stop Codex/Claude processes. They remain independently launched clients.

## Boundaries

- `compose down` preserves named volumes; removing the database volume destroys live data.
- Build-time internet access is separate from runtime provider access.
- The checked-in `compose.yaml` starts the web, API, database, migration, and maintenance services. The [project index](../README.md) covers browser pairing and client configuration.
- A future automatic launch path requires a separately confirmed launcher/readiness contract and implementation ticket.

[History rules](document-history.md) · [Log retention](activity-logging.md) · [Trust boundaries](security.md)
