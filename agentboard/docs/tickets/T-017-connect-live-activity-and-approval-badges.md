---
name: "T-017 — Connect live activity and approval request displays"
description: "The logging page and approval badges stay current using committed server data."
kind: "ticket"
tags: ["feature:progress-tracking", "feature:task-coordination", "feature:agent-role-management", "concern:auditability", "concern:authorization", "concern:reliability", "concern:privacy"]
---

# T-017 — Connect live activity and approval request displays

Role: FE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-007, T-008, T-011, T-013
Estimate (days): 2
Estimate scope: Build
Estimate basis: Provisional: existing activity/badge components reused; live-state integration, browser checks and review.

## Outcome
The logging page and approval badges stay current using committed server data.

## Acceptance Criteria
- Wire existing Activity filters including clickable agent/label controls to server queries and distinguish reported versus observed events.
- Use SSE notifications to refetch activity, task changes and request state; preserve older-log scroll and offer buffered new events.
- Show Needs approval independently of task status with actual request details; do not add a browser approval inbox or approve endpoint.
- Test multiple pending requests, unsupported/rejected/stale outcomes, disconnect/reconnect/expired cursors and unavailable data without fabricated success.

## Context
- [US-010](../user-stories/US-010-review-a-task-s-changes.md)
- [US-012](../user-stories/US-012-approve-agent-updates-and-deletions-in-the-client.md)
- [US-013](../user-stories/US-013-report-and-review-agent-activity.md)
- [US-014](../user-stories/US-014-expire-activity-after-30-days.md)
- [activity-logging](../technical-architecture/activity-logging.md)
- [approval-flow](../technical-architecture/approval-flow.md)
- [security](../technical-architecture/security.md)
- [Approved screen inventory](../designs/screens/README.md)
- [Existing implementation](../../frontend/src/features/activity/ActivityScreen.tsx)
- [Assigned role](../../agents/frontend-programmer.md)

## Dependencies
- [T-007](T-007-record-filter-and-expire-activity.md)
- [T-008](T-008-enforce-client-approved-mutations.md)
- [T-011](T-011-stream-committed-project-events.md)
- [T-013](T-013-connect-frontend-to-authenticated-api.md)
