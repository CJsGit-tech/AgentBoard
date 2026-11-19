---
name: "T-004 — Persist tickets, responsibility and progress"
description: "Saved tickets expose correct ownership, status, priorities, blockers and derived project progress."
kind: "ticket"
tags: ["feature:task-coordination", "feature:progress-tracking", "concern:data-integrity", "concern:auditability"]
---

# T-004 — Persist tickets, responsibility and progress

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-002, T-003
Estimate (days): 2.5
Estimate scope: Build
Estimate basis: Provisional: core ticket/progress services and regression tests/review; links, agent approval and planning metadata have separate tickets.

## Outcome
Saved tickets expose correct ownership, status, priorities, blockers and derived project progress.

## Acceptance Criteria
- Implement ticket create/read/update/delete and project-scoped list/filter/order behavior against the contract, including retry-safe creation.
- Enforce nonblank titles, same-project role/self/unassigned ownership and blocker explanations; preserve unrelated fields on edits.
- Store revision-checked updates and previous/new ownership/status audit values atomically; failed changes create no success audit.
- Compute project counts from committed records, keeping approval indicators distinct from Planned/In Progress/Blocked/Done; test conflicts and isolation.

## Context
- [US-004](../user-stories/US-004-create-and-prioritize-tasks.md)
- [US-005](../user-stories/US-005-assign-task-responsibility.md)
- [US-006](../user-stories/US-006-track-task-progress-and-blockers.md)
- [US-009](../user-stories/US-009-review-project-progress.md)
- [US-010](../user-stories/US-010-review-a-task-s-changes.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [data-model](../technical-architecture/data-model.md)
- [activity-logging](../technical-architecture/activity-logging.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-002](T-002-persist-projects-and-agent-roles.md)
- [T-003](T-003-authorize-local-browser-and-agent-clients.md)
