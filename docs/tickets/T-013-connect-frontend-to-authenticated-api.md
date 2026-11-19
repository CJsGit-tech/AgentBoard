---
name: "T-013 — Connect frontend data access to authenticated REST"
description: "The existing React app can load/save canonical server records through an isolated production adapter."
kind: "ticket"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:security", "concern:privacy", "concern:reliability"]
---

# T-013 — Connect frontend data access to authenticated REST

Role: FE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-003
Estimate (days): 2
Estimate scope: Build
Estimate basis: Provisional: common adapter/session/error infrastructure and tests/review; feature wiring and actual end-to-end flows separate.

## Outcome
The existing React app can load/save canonical server records through an isolated production adapter.

## Acceptance Criteria
- Replace direct fixture coupling through a typed adapter boundary; preserve fixtures for explicit mock tests/previews and never silently fall back to them after API failures.
- Map wire IDs, field names/status casing, revisions and structured errors to the existing UI model; handle sessions/CSRF through the browser contract.
- Implement honest loading/empty/error states and retain drafts on rejected/unavailable writes without optimistic false success.
- Test adapter mappings, unauthorized/expired-session behavior and stale-response project switching; keep the approved shell and meaningful component boundaries.

## Context
- [source-layout](../technical-architecture/source-layout.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [security](../technical-architecture/security.md)
- [Approved screen inventory](../designs/screens/README.md)
- [Existing implementation](../../frontend/src/app/WorkspaceContext.tsx)
- [Assigned role](../../agents/frontend-programmer.md)

## Dependencies
- [T-003](T-003-authorize-local-browser-and-agent-clients.md)
