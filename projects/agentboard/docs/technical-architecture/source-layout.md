---
name: "Frontend and backend folder plans"
description: "Locate responsibilities without imposing application code."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:reliability", "concern:security"]
---

# Frontend and backend folder plans

> Owner: Solution Architect | Version: 0.1.3 | Status: draft | Last Updated: 2026-11-18

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
    main.py                   # REST, browser session, SSE, MCP mount
    api/                      # projects and roles
    artifacts/                # tickets, documents, history and links
    auth/                     # browser pairing and sessions
    mcp/                      # tool catalog, client auth and approvals
    schemas/
    services/                 # activity and idempotency
    db/                       # SQLAlchemy models and connections
    maintenance/              # retention jobs
  migrations/                 # Alembic
compose.yaml                  # locally hosted runtime
infra/
  web.Dockerfile
  backend.Dockerfile
  proxy.conf
  init-secrets.py
  backup.sh
```

**Run:** Follow the [project run instructions](../README.md).

[Interfaces](api-contracts.md) · [Approval behavior](approval-flow.md)
