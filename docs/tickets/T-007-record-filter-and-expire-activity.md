---
name: "T-007 — Record, filter and expire activity after 30 days"
description: "Minimal agent/ticket activity remains queryable for a rolling 30 days and expires safely."
kind: "ticket"
tags: ["feature:progress-tracking", "feature:task-coordination", "feature:agent-role-management", "concern:auditability", "concern:retention", "concern:privacy", "concern:reliability"]
---

# T-007 — Record, filter and expire activity after 30 days

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-001, T-003, T-004
Estimate (days): 3
Estimate scope: Build
Estimate basis: Provisional: query/append services and maintenance worker plus clock-controlled integration tests/review.

## Outcome
Minimal agent/ticket activity remains queryable for a rolling 30 days and expires safely.

## Acceptance Criteria
- Persist filterable server-observed and agent-reported events with agent, optional actual ticket, action, outcome, labels and authoritative received_at.
- Deduplicate event keys without recursively auditing the activity append; exclude secrets, prompts, document bodies and full tool payloads.
- Enforce the 30-day query cutoff immediately, including after downtime; run bounded locked cleanup without deleting live business records.
- Test retention boundary timestamps, duplicate deliveries, failed-operation provenance and filters; record chosen cleanup/pending-request expiry cadence as an implementation proposal.

## Context
- [US-010](../user-stories/US-010-review-a-task-s-changes.md)
- [US-013](../user-stories/US-013-report-and-review-agent-activity.md)
- [US-014](../user-stories/US-014-expire-activity-after-30-days.md)
- [activity-logging](../technical-architecture/activity-logging.md)
- [security](../technical-architecture/security.md)
- [deployment-operations](../technical-architecture/deployment-operations.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-001](T-001-establish-backend-and-database.md)
- [T-003](T-003-authorize-local-browser-and-agent-clients.md)
- [T-004](T-004-persist-tickets-and-progress.md)
