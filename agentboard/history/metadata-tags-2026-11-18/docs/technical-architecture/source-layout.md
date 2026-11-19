# Frontend and backend folder plans

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Locate responsibilities without imposing application code.

## Frontend Folder Structure

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

- Preserve UI drafts after failed saves.
- Refetch after live notifications; never display pending changes as committed.
- Show request details on the ticket badge; approval happens in a capable agent client, not an app-wide approval inbox.

## Backend Folder Structure

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

**Status:** Folder plans only; no application code was generated.

[Interfaces](api-contracts.md) · [Approval behavior](approval-flow.md)
