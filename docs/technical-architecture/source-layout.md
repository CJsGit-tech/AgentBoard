---
name: "Source Layout"
description: "Maps the current AgentBoard source tree to its runtime responsibilities."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:reliability", "concern:security"]
---

# Source Layout

This page describes the checked-in implementation. Follow the [setup guide](../../README.md) to run it.

```text
backend/
  app/                  FastAPI API, MCP server, auth, services, and models
  migrations/           Alembic database migrations
  tests/                Backend unit tests
frontend/
  src/                  React app, feature screens, and API clients
  tests/                Browser UI tests
infra/                  Docker build, secret initialization, and backups
docs/                   Product, design, security, API, and operations docs
agents/                 Agent role prompts
agentboard-skill/       Separate reusable AgentBoard project skill
compose.yaml            Local multi-service deployment
```

The backend Docker image builds the frontend and serves its static files beside FastAPI. PostgreSQL stores application records. Compose runs migrations before the backend and runs activity cleanup in a separate maintenance service.

[API contracts](api-contracts.md) · [Deployment and operations](deployment-operations.md) · [Security](security.md)
