# Technical Architecture — AgentBoard

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## 1. Scope & Architecture Summary

AgentBoard is a single-user local web app. React/Vite provides the interface, FastAPI provides browser APIs and an MCP interface, and a local Postgres service stores projects, role definitions, tickets, documents, recent revisions, approvals, and activity. Docker Compose manages the services. Codex and Claude operate independently; they use MCP tools to read/create records, request approved updates/deletions, and report external work. AgentBoard does not launch, stop, or supervise agent processes.

This revision supersedes the earlier SQLite/single-container proposal. It adds the confirmed agent-facing integration, approval gate, live activity page, and bounded history. It remains a design document; no application or infrastructure code has been built.

## 3. High-Level System Architecture

Diagram: [system-architecture.svg](./system-architecture.svg).

Services:

- `web`: static Vite build served through an HTTP reverse proxy. Only published port: `127.0.0.1:8080`. Routes `/api/`, `/mcp`, and `/events` to the backend, preserving streaming; browser navigation falls back to the SPA while unknown API routes remain JSON errors.
- `backend`: FastAPI, browser REST, authenticated MCP tools, approval mediation, revision services, and event streaming. Internal port `8000`; not published directly. Browser and MCP adapters invoke the same application services.
- `db`: Postgres, internal port `5432`, no published host port, persistent named volume `agentboard_pgdata`.
- `maintenance`: lightweight Python service from the backend image, scheduled log expiry and startup cleanup. Same schema but no network listener; no Redis or queue needed for this scope.
- `migrate`: one-shot schema migration service. Depends on database health; backend/maintenance wait for its successful completion.

Five aligned functional modules appear in both UI and backend: (1) Projects, (2) Agent Roles, (3) Tickets, (4) Documents, (5) Activity & Progress. Shared approval enforcement sits before agent mutations, not inside UI-only logic. A Needs approval badge is derived from pending requests associated with a ticket; it never replaces the task's status.

Browser: same-origin requests and SSE → reverse proxy → FastAPI → transactional services → Postgres. External Codex/Claude: Streamable HTTP MCP → same proxy/backend → the same services. A thin stdio bridge may be supplied for clients whose tested configuration requires stdio. It forwards capabilities, cancellation, and approval interactions; it does not create a second database or bypass authorization. Native client and bridge behavior must be tested separately.

Online providers: N/A. AgentBoard never needs the clients' model API keys. The AgentBuild planning folder remains separate from runtime data; automatic import is not included.

## Read Only the Topic You Need

- [Environment and discovery](constraints.md)
- [Technology stack and tradeoffs](technology-stack.md)
- [Data model and transactions](data-model.md)
- [Document history and restore](document-history.md)
- [Activity logging and 30-day retention](activity-logging.md)
- [Agent Update/Delete approval flow](approval-flow.md)
- [Browser REST contracts](api-contracts.md)
- [MCP tools, approvals and client compatibility](mcp-tools.md)
- [Frontend and backend folder plans](source-layout.md)
- [Security and nonfunctional requirements](security.md)
- [Compose, migration, backup and recovery](deployment-operations.md)
- [Architectural decision records](decisions.md)
- [Open risks and official sources](risks-and-references.md)

For agent ticket changes, read the relevant [story](../user-stories/README.md), then [approval behavior](approval-flow.md) and [API contracts](api-contracts.md). For document revisions, read [data rules](data-model.md) and the applicable MCP tool.

[User Stories](../user-stories/README.md) · [Product Vision](../product-vision.md)
