---
name: "T-011 — Stream committed project events with safe reconnect"
description: "Browser clients receive project-scoped committed notifications and recover after interruptions."
kind: "ticket"
tags: ["feature:progress-tracking", "feature:task-coordination", "concern:reliability", "concern:auditability"]
---

# T-011 — Stream committed project events with safe reconnect

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-003, T-007, T-008
Estimate (days): 2
Estimate scope: Build
Estimate basis: Provisional: single-worker persisted replay baseline, SSE recovery tests and review; proxy behavior covered in deployment.

## Outcome
Browser clients receive project-scoped committed notifications and recover after interruptions.

## Acceptance Criteria
- Implement /events with retained event IDs, authorization, project filters and canonical refetch notifications; exclude document bodies.
- Resume retained cursors; signal an expired/missing interval and require resync rather than replaying expired activity.
- Emit only committed events and test rollback, disconnection, restart and expired-cursor behavior.
- Record measured local notification latency separately from the proposed under-two-second goal; no unsupported performance claim.

## Context
- [US-009](../user-stories/US-009-review-project-progress.md)
- [US-012](../user-stories/US-012-approve-agent-updates-and-deletions-in-the-client.md)
- [US-013](../user-stories/US-013-report-and-review-agent-activity.md)
- [US-014](../user-stories/US-014-expire-activity-after-30-days.md)
- [security](../technical-architecture/security.md)
- [activity-logging](../technical-architecture/activity-logging.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-003](T-003-authorize-local-browser-and-agent-clients.md)
- [T-007](T-007-record-filter-and-expire-activity.md)
- [T-008](T-008-enforce-client-approved-mutations.md)
