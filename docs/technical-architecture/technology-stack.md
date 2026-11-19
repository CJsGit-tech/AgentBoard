---
name: "Technology Stack"
description: "Record selected technologies, proposed libraries and their tradeoffs."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:reliability", "concern:compatibility", "concern:security"]
---

# Technology Stack

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Record selected technologies, proposed libraries and their tradeoffs.

## Technology & SDK Decisions

| Layer | Choice / status | Why | Tradeoff / alternative |
| --- | --- | --- | --- |
| UI | **Confirmed:** React/Vite. **Proposed:** TypeScript | Reusable board/editor components | SPA state/error handling; server templates simplify basic forms |
| API | **Confirmed:** Python FastAPI. **Proposed:** Pydantic/Uvicorn | Typed contracts and Python integration | Streaming/lifecycle coordination; Django offers more built-in administration |
| MCP | **Proposed:** official Python SDK, pinned tested release | Standard typed tools and capability negotiation | Client differences; tool annotations do not enforce approval |
| Data | **Confirmed:** Postgres. **Proposed:** SQLAlchemy/psycopg/Alembic | Transactions and concurrent agent writes | More memory/startup/backup work than SQLite; accepted database tradeoff |
| Live UI | **Proposed:** SSE with persisted event IDs | One-way live updates and reconnectable HTTP | Buffering/timeouts need tests; no bidirectional WebSocket requirement yet |
| Delivery | **Confirmed:** Compose. **Proposed:** separate services/helper jobs | Shared browser/MCP services with explicit boundaries | More containers than an embedded design |

## Verification

Exact versions and interoperability are unverified. Test SDK elicitation against negotiated client capabilities; MCP support alone does not prove approval support.

[Official references](risks-and-references.md) · [Deployment](deployment-operations.md)
