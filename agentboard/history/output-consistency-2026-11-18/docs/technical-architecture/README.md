# Technical Architecture — AgentBoard

> Owner: Solution Architect | Version: 0.1.3 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Understand the system, then open only the topic needed for the task.

## Scope & Architecture Summary

AgentBoard is a single-user local web app for projects, agent roles, tickets, documents and activity. Codex/Claude operate it through MCP; they run independently. This is a design draft, not a built or tested application.

| Confirmed | Proposed implementation |
| --- | --- |
| Personal computer; Docker Compose | Separate web/backend/database and helper services |
| React/Vite, Python FastAPI, local Postgres | SQLAlchemy/psycopg/Alembic; SSE; exact ports |
| Agent Create/Read freely; Update/Delete approved in client | Capability-tested client approval mediation |
| Current document + three previous versions; 30-day logs | Transactional pruning and scheduled cleanup |

## High-Level System Architecture

[Open module diagram](system-architecture.svg)

```text
Browser ── REST / live events ──┐
                              ├→ web proxy → FastAPI services → Postgres
Codex / Claude ── MCP ─────────┘                    ↑
                                          client approval for U/D
```

Five functional modules: **Projects · Agent Roles · Tickets · Documents · Activity & Progress**.

- **Needs approval** is a separate badge, never a task status.
- No hosted infrastructure providers or shared model keys.
- No agent launch/stop controls or automatic import of AgentBuild planning files.
- The earlier SQLite/single-container proposal is superseded.

## Read Only the Topic You Need

| Task | Read |
| --- | --- |
| Check confirmed scope and assumptions | [Constraints](constraints.md) |
| Understand stack choices | [Technology](technology-stack.md) |
| Implement entities and transactions | [Data model](data-model.md) |
| Change or delete records through an agent | [Approval flow](approval-flow.md) → [MCP tools](mcp-tools.md) |
| Implement document revisions or restore | [Document history](document-history.md) |
| Implement activity feed or expiry | [Activity logging](activity-logging.md) |
| Implement HTTP operations | [API contracts](api-contracts.md) → [OpenAPI JSON](contracts/openapi.json) |
| Locate frontend/backend responsibilities | [Source layout](source-layout.md) |
| Review access, privacy, live delivery and test requirements | [Security & nonfunctional requirements](security.md) |
| Start, upgrade or recover the application | [Deployment & operations](deployment-operations.md) |
| Inspect exact fields or example payloads | [Contracts](contracts/README.md) · [JSON examples](examples/README.md) |
| Understand rationale or remaining verification | [Decisions](decisions.md) · [Risks & references](risks-and-references.md) |

[User Stories](../user-stories/README.md) · [Product Vision](../product-vision.md)
