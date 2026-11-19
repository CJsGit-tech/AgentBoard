# Technical Architecture — AgentBoard

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17
> Based on: Product Vision v0.1.2; User Stories v0.1.2; confirmed discovery brief in this conversation

## 1. Scope & Architecture Summary

AgentBoard is a single-user local web app. React/Vite provides the interface, FastAPI provides browser APIs and an MCP interface, and a local Postgres service stores projects, role definitions, tickets, documents, recent revisions, approvals, and activity. Docker Compose manages the services. Codex and Claude operate independently; they use MCP tools to read/create records, request approved updates/deletions, and report external work. AgentBoard does not launch, stop, or supervise agent processes.

This revision supersedes the earlier SQLite/single-container proposal. It adds the confirmed agent-facing integration, approval gate, live activity page, and bounded history. It remains a design document; no application or infrastructure code has been built.

## Discovery Record

Multiple discovery rounds established local-only deployment, a single builder, React/Vite, Python, Postgres, and no hosted infrastructure providers. The owner confirmed FastAPI and authorized this revision after reviewing the complete brief. External model access stays with Codex/Claude. Agents may Create/Read without per-operation approval; Update/Delete require approval through the client interface. Unsupported approval must not execute changes. Tickets show a separate Needs approval badge. Logs are minimal, labeled, live, and retained for 30 days. Documents live in Postgres with a current version plus three previous versions, accessible to agents.

Proposed implementation details below include service separation, transport adapters, SQLAlchemy/Alembic, SSE, exact ports, cleanup cadence, and concurrency controls. These refine the brief and require implementation verification, rather than representing tested software.

## 2. Environment & Constraints

| Area | Constraint / decision | Status |
| --- | --- | --- |
| Deployment | Personal computer only; Docker Compose; one user | Confirmed |
| Frontend / backend / database | React + Vite / Python FastAPI / local Postgres | Confirmed |
| Agent clients | Codex desktop, Codex CLI, Claude Code, Claude Desktop | Required compatibility targets, not yet tested |
| Providers | No hosted database, identity, storage, or deployment service | Confirmed |
| Host / browsers | Desktop browser; validate macOS arm64 first, then other claimed targets | Proposed validation order |
| Agent lifecycle | External; only MCP operations and activity reporting | Confirmed |
| Offline use | Core app works after local installation without internet; external agents may need their own connectivity | Design requirement |
| Capacity | Initial test envelope: 100 projects, 10,000 tickets, 1,000 documents; 10 concurrent MCP connections | Proposed benchmark envelope |

No installed library versions or client capability matrix have been verified. Pin supported package/image versions during implementation; negotiate a tested common MCP protocol version rather than assume all clients support the newest specification.

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

## 4. Technology & SDK Decisions

| Layer | Selection | Pros / reason | Cons / alternative |
| --- | --- | --- | --- |
| UI | React, TypeScript, Vite | Confirmed preference; reusable editors and board modules | SPA state/error handling needed; server templates simpler for small forms |
| API | FastAPI, Pydantic, Uvicorn | Confirmed; typed contracts, Python MCP integration boundary | Requires deliberate lifecycle/streaming coordination; Django offers more built-in administration |
| MCP | Official Python MCP SDK, pinned to tested release | Standard tool schemas and negotiated client capabilities | Client/version differences require adapters and integration tests; tool annotations alone do not enforce approval |
| Persistence | Postgres, SQLAlchemy, psycopg, Alembic | Confirmed database; transactional approval/revision/event writes and concurrency | More RAM, startup, and backup work than SQLite; accepted tradeoff after owner discussion |
| Live UI | SSE with persisted event IDs | One-way live updates fit the activity board; reconnectable HTTP | Proxy buffering/timeouts require testing; WebSocket unnecessary until bidirectional requirements emerge |
| Local delivery | Separate web, backend, db; maintenance and migration helpers | Explicit module/container boundaries and repeatable lifecycle | More containers than the superseded embedded design |

React/Vite, FastAPI, and Postgres are selected; exact versions and dependency interoperability remain unverified. SDK support for elicitation must be checked against the negotiated protocol/client capabilities, not inferred from the existence of MCP tools. Official references are listed at the end.

## 5. Data & Storage Design

Server-generated UUIDs; UTC timestamps; mutable domain rows carry integer revision and created_at/updated_at. Project IDs constrain related records through composite foreign keys. Store document bodies as text in Postgres, not host Markdown files.

| Entity | Essential data and invariants |
| --- | --- |
| Project | Name, purpose; nonblank name; duplicate names distinguished by ID and visible creation detail |
| AgentRole | Project, name, responsibilities; role definitions do not imply a running process |
| Ticket | Project, title, description, priority, status, owner_kind, role_id, blocker_reason, revision |
| Document / DocumentVersion | Current content and version ID; previous content, version ID, author/source, timestamp; at most three previous versions per document |
| TicketDocument | Same-project ticket/document association; relationship context/output; unique tuple |
| AgentClient | Local credential identifier and declared client/agent label; client labels are attribution, not cryptographic proof of a human identity |
| MutationRequest | Target/project/ticket association, operation, exact proposed patch or deletion, base revision, payload hash, requester, status, creation/expiry/decision times |
| ActivityEvent | Server ID, deduplication key, project, optional ticket, agent/client, action/event_type, outcome, labels, occurred_at, received_at, provenance |

Ticket status remains Planned / In Progress / Blocked / Done. Approval is a separate indicator derived from one or more pending MutationRequests. A document or project mutation without a ticket stays visible on its record/activity; agents may supply a same-project ticket association. Never invent a ticket to attach a request.

Agent CR is permitted without per-operation approval after local connection authorization. An update is still an update if expressed as restore, link replacement, or status completion. Creating a new document is allowed; overwriting an existing document cannot be disguised as Create. Existing link removal requires approval; adding a genuinely new association is Create. Human actions in the local web UI are explicit user operations and do not need a second agent approval prompt.

Document changes lock/check the current revision, preserve the outgoing content, commit the new current version, then prune older history to the newest three previous versions in the same transaction. Restore copies a retained version into a new current version, obeying the same bound. Compare is read-only; agents can read and compare all retained content. Current document timestamp changes only on successful content updates. Deleted document bodies and versions are removed together; retain only minimal deletion metadata in the bounded event log. No hidden unbounded revision archive.

Activity logs cover server-observed operations plus agent-reported dispatch/tool/work events; full external capture is explicitly not promised. Minimal payload: agent, ticket if relevant, action, outcome, timestamps, labels, provenance. No full prompts, tool arguments, results, document bodies, or secrets by default. Recording a log event must not recursively log its own log write forever.

Use server received_at as the retention clock; preserve reported occurred_at for display and label it as reported. All activity queries/SSE replay enforce received_at > server_now - 30 days, regardless of cleanup lag. Maintenance deletes expired rows in bounded batches at least hourly and immediately at startup. Task history uses the same events and retention. Prune terminal approval audit details after 30 days; pending approval payloads expire after a proposed 24 hours and are purged, with a visible expired outcome. Exact operational retention cadence is a proposal; content remains inaccessible after expiry even if the machine was stopped. Backups are separate point-in-time copies and must have their own bounded retention; restored data is filtered/cleaned before serving.

Indexes: project/status, project/priority, document/project, activity received_at, project/ticket/agent/event_type/time, labels as suitable JSONB/GIN or normalized labels after measurement, and pending requests by ticket/status. Use row locks and revision checks for agent commits; no mutable progress counters. A successful operation and its automatic audit event commit together.

## 6. API / Interface Contracts

### Browser REST

Prefix `/api/v1`. Project-scoped resource collections: `/projects`, `/projects/{p}/roles`, `/projects/{p}/tickets`, `/projects/{p}/documents`. Collection GET/POST and individual GET/PATCH/DELETE implement explicit supported operations; project/role/ticket deletion behavior is constrained below. Additional routes:

- `/projects/{p}/tickets/{t}/documents`: list/create associations; targeted DELETE removes the link only.
- `/projects/{p}/documents/{d}/versions`: list/read retained versions; `/compare` accepts two retained IDs; `/restore` creates a new current version.
- `/projects/{p}/progress`: counts by status plus separate pending-approval counts.
- `/projects/{p}/activity`: filters by ticket, agent, event_type, labels, time, outcome, provenance.
- `/mutation-requests/{id}`: read request/result; browser provides visibility, not an agent-approval inbox or approve endpoint.
- `/events`: same-origin SSE with project filters, retained event IDs and reconnect cursor. Client refetches canonical records after notifications; no document bodies in events.

Delete semantics: document deletion removes its versions and associations; ticket deletion removes its associations/pending requests and retains only bounded audit metadata; role deletion is rejected while assigned; project deletion is rejected while it contains records in this release. Every agent deletion goes through client approval. Explicitly describe consequences in the approval summary. Never silently cascade deletion of a populated project.

Create returns 201, reads/updates 200, successful deletion 204. Invalid fields 422, missing/cross-project resource 404, stale revision 409, authorization failure 401/403, temporary database failure 503. Errors: `{error: {code, message, fields}, request_id}`. Revision-required mutations reject stale writes rather than overwrite. Bounded pagination default 50/max 100, deterministic tie-break by ID. Creates accept client operation keys; same key+payload returns the prior result, different payload returns conflict. Reference limits proposed: 1 MiB document; 2 KiB activity summary; bounded labels. Rejected input preserves the UI draft.

### MCP tools

Typed JSON input/output; same project checks, services, error codes, concurrency and idempotency rules as REST. Initial explicit tool families:

| Family | Tools / behavior |
| --- | --- |
| Projects | list_projects, get_project, create_project, update_project, delete_project |
| Roles | list_roles, get_role, create_role, update_role, delete_role |
| Tickets | list_tickets, get_ticket, create_ticket, update_ticket, delete_ticket; status/owner edits are updates |
| Documents | list_documents, get_document, create_document, update_document, delete_document; link_document, unlink_document |
| History | list_document_versions, get_document_version, compare_document_versions, restore_document_version |
| Activity | append_activity, list_activity, get_project_progress |
| Approvals | get_mutation_request, retry_mutation_request (re-runs client approval for unchanged pending payload) |

No agent-callable approve tool, `approved=true` flag, or arbitrary SQL/shell tool. Reads and creates execute freely under an authenticated local client credential. Agent U/D tools first persist a pending request and return/emit its identity; when verified user elicitation is available, they present the target, exact change/deletion consequence, and base revision in the client UI. Accept applies that payload atomically; decline/cancel/expiry does not execute. Unsupported elicitation returns `approval_required` plus request ID and keeps the ticket badge pending for a later capable-client retry. A disconnected call is never evidence of approval.

Approval is tied to server-controlled request identity, authenticated client connection, target, payload hash, base revision, expiration and a single-use decision. An agent's textual claim of approval is not accepted. If native client confirmation is to be used instead of elicitation, it requires a separately verified integration that conveys a trustworthy user decision; showing a generic tool prompt alone is insufficient for the server to infer permission. The trusted client is still part of the security boundary; this cannot protect against a malicious client that fabricates human responses.

Concurrent record changes invalidate outstanding approvals. Commit uses the approved base revision and rejects stale requests; retries need a new user decision. Clearing a single request removes Needs approval only when no other pending request remains. Backend never holds a database transaction open while waiting for human input. Short bounded approval interactions can resolve inline; longer or unsupported interactions return request IDs and stay queryable.

### Transport and client verification

Prefer authenticated loopback Streamable HTTP at `/mcp`. For stdio-only client configurations, provide a local bridge that relays protocol features without interpreting untrusted text as approval. Register each integration locally with a scoped credential; no hosted identity provider. Keep browser cookie/CSRF and MCP credentials separate. Validate HTTP Origin/Host; reject unauthenticated connections.

Compatibility release gate per Codex desktop, Codex CLI, Claude Code, and Claude Desktop: initialization/version negotiation; list/call tools; CR; approval accept/decline/unsupported; restart/reconnect; duplicate call; stale mutation; revision reads; activity append. Until these tests run, do not claim universal working support. Older and newer protocol versions differ; choose SDK and protocol versions from actual client support. All adapters must fail closed for unsupported approval.

## 7. Frontend Folder Structure

```text
frontend/
  src/
    app/                       # navigation, selected project, connection state
    features/
      projects/
      roles/
      tickets/                 # status and separate Needs approval badge
      documents/               # editor, history, comparison, restore
      activity/                # labels, filters, live stream, progress
    components/                # accessible controls and error/empty states
    api/                       # REST and SSE clients; revision handling
    tests/
  package.json
```

UI drafts survive failed saves; pending agent changes never appear as committed content. Live notifications invalidate/refetch views. No app-wide native approval inbox is introduced. A pending ticket badge exposes request details and tells the builder to approve through a capable agent client.

## 8. Backend Folder Structure

```text
backend/
  app/
    main.py
    api/                       # browser routes, errors, SSE
    mcp/                       # tools, transport, approval interactions
    auth/                      # browser session, MCP credentials, Origin checks
    schemas/
    services/
      projects.py
      roles.py
      tickets.py
      documents.py
      approvals.py
      activity.py
    repositories/
    db/                        # SQLAlchemy models, connection management
    maintenance/               # retention and expiry loop
  migrations/                  # Alembic
  tests/
adapters/
  stdio/                       # optional thin protocol bridge
infra/
  compose.yaml
  compose.dev.yaml
  web.Dockerfile
  backend.Dockerfile
  proxy.conf
```

These are implementation plans only; no folders or application code are generated by this command.

## 9. Security & Nonfunctional Requirements

Local OS account is trusted; loopback-only exposure is required, not an authentication substitute. First-run local pairing creates browser session and per-client credentials. No shared model/provider keys. Restrict credential files; validate HTTP Host/Origin, content types, request sizes, and CSRF on browser mutations. MCP tools cannot impersonate browser user actions. Do not expose a generic agent-accessible route that bypasses approval. Run containers non-root where supported, without host Docker socket or arbitrary host filesystem access. Render document Markdown with raw HTML disabled and safe links.

Event provenance is visible: API-observed, MCP-observed, agent-reported, maintenance. Agent-reported identity/times are not presented as independent verification. Logs default to minimal metadata. Operator/container logs must also be rotated and expire within 30 days; redact bodies/tokens, and avoid adding a second durable full-payload log. Exclude sensitive payloads from pending-request audit metadata after resolution.

Live delivery uses SSE plus Postgres as the source of truth; proposed one backend worker initially. Poll retained event IDs for correctness across backend/maintenance processes; future LISTEN/NOTIFY can reduce latency without replacing persisted replay. Reconnect resyncs canonical records when a cursor has expired. Proposed live target under two seconds locally; benchmark rather than claim achieved performance.

Tests cover US-001–015: project isolation, atomic mutations/events, unsupported approval and visible badge, multiple pending requests, stale or replayed approval, rejected deletes, idempotent CR/log append, document history pruning under concurrent writes, restoring creates a new version, retention after downtime, SSE recovery, and failed save recovery. Proposed reference workload is the envelope in section 2; select the benchmark machine and budgets during implementation. Keyboard and non-color-only status/badges are required.

## 10. Deployment & Operations

Compose network: web ↔ backend ↔ db; maintenance/migrate reach db. Only web publishes loopback port. Use healthchecks and dependency conditions: db healthy → migrate success → backend/maintenance; web proxies only to ready backend and shows an explicit unavailable state otherwise. Docker documents that startup order alone does not establish readiness.

Pin image and dependency versions after testing; use a stable Compose project/volume name. Secrets come from local restricted configuration or mounted secret files, not source control or frontend build variables. Vite's production build runs in a Node image stage; production web serves static assets. Alembic migrations run once as a Compose job; no concurrent worker migrations. Startup cleans/filters expired events before serving. Maintenance uses a database lock to avoid duplicate cleanup if restarted twice.

Backup proposal: daily local `pg_dump` archive outside the data volume, rolling retention no longer than 30 days; matching roles/setup configuration stored separately without exposing secrets. A dump can provide a consistent single-database export, but backup validity requires restore tests. Restore into a fresh volume, apply startup expiry and revision limits, then test document reads and task counts before switching. Historical backups may contain subsequently pruned revisions until backup expiry; the live API always exposes only current+three previous versions. Clarify stricter physical erasure needs before implementation if that is unacceptable.

Rollback uses the matching pre-upgrade database backup; older images are not assumed compatible with newer schemas. Compose down preserves named volumes; removing the database volume destroys live data. Build-time internet access is distinct from runtime provider access. No containers have been started or client integrations configured in this task.

## 11. Architectural Decisions

| ID | Decision | Rationale / revision | Related stories |
| --- | --- | --- | --- |
| ADR-001 | Local web app via Docker Compose | Confirmed, single personal-computer deployment | US-001–015 |
| ADR-002 | Separate web/backend/db with helper jobs | Revises previous combined-container proposal for module clarity and shared browser/MCP backend | US-001–015 |
| ADR-003 | Local Postgres | Supersedes SQLite proposal after explicit owner selection | US-001–015 |
| ADR-004 | External agents operate through MCP and report activity | Replaces manual-only integration boundary; no process management | US-003, US-005, US-011–013 |
| ADR-005 | Revision checks plus atomic audit writes | Preserves previous concurrency decision; extends to approvals | US-006–007, US-010–012, US-015 |
| ADR-006 | Project-scoped APIs and database constraints | Preserves project isolation | US-002, US-005, US-008–009, US-011 |
| ADR-007 | Client approval for U/D; separate badge | Confirmed; unsupported approval does not mutate | US-012 |
| ADR-008 | Minimal labeled activity, live SSE, 30-day expiry | Confirmed behavior; SSE/maintenance mechanism proposed | US-010, US-013–014 |
| ADR-009 | Current plus three prior document versions | Confirmed; agent-readable history and approved restore | US-007, US-015 |

Preserve ADR IDs across revisions. Confirmed product decisions do not automatically approve this document or its proposed implementation details.

## 12. Open Risks & Decisions

Implementation verification: client-specific MCP capability/approval tests may reveal that some targets support only CR until adapters are available; never weaken approval to claim compatibility. Owner-approved brief is sufficient to author this draft; exact SDK protocol versions, image versions, host matrix, backup timing, resource budgets, and schema performance remain implementation validation tasks. Design Profile must show logging filters, document comparisons and separate task/approval indicators.

Project Vision is intentionally concise and unchanged by this request. New stories trace MCP/approvals/logging/history to its existing role, task, document and progress features. No hosted services or paid provider integrations were introduced.

Official references consulted 2026-11-17:

- [MCP transports](https://modelcontextprotocol.io/specification/latest/basic/transports) — stdio and Streamable HTTP bindings; verify against the version selected for clients.
- [MCP elicitation](https://modelcontextprotocol.io/specification/latest/client/elicitation) — user interaction and negotiated client support; does not guarantee every client's approval UI.
- [Official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk) — pin and test a supported release.
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/) — health and completed-job conditions.
- [Postgres pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html) — consistent database export and restore formats.
