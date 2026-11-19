---
name: "T-012 — Package local Compose deployment and recovery"
description: "The app's first install/run path is documented Docker Compose with retained data and recovery guidance."
kind: "ticket"
tags: ["concern:reliability", "concern:privacy", "concern:security"]
---

# T-012 — Package local Compose deployment and recovery

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-009, T-011
Estimate (days): 3
Estimate scope: Build
Estimate basis: Provisional: local images/proxy/startup, recovery exercise and review; exact versions/host availability remain implementation checks.

## Outcome
Docker Compose is the first install/run path for the app, with retained data and documented recovery.

## Acceptance Criteria
- Package web/backend/db/migrate/maintenance services with pinned tested images, readiness order, named storage and no exposed database/backend ports.
- Document the user's Compose-based install/start and connection to the web and MCP endpoints. Automatic AgentBuild process launch/readiness probing is undefined and deferred; do not add a launcher or imply the skill starts containers.
- Expose only the chosen loopback web port; proxy /api, /mcp and /events with streaming and correct SPA/API fallback behavior.
- Test install, migration failure, restart persistence and maintenance startup on an explicitly recorded host; do not claim untested host support.
- Demonstrate backup restoration into a fresh volume with history/activity limits applied before serving, bounded log/backup retention and documented destructive-volume warnings.

## Context
- [US-014](../user-stories/US-014-expire-activity-after-30-days.md)
- [deployment-operations](../technical-architecture/deployment-operations.md)
- [security](../technical-architecture/security.md)
- [constraints](../technical-architecture/constraints.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-009](T-009-expose-typed-mcp-tools.md)
- [T-011](T-011-stream-committed-project-events.md)
