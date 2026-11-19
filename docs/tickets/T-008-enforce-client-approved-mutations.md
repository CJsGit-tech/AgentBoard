---
name: "T-008 — Enforce verified client approval for agent mutations"
description: "Agent Update/Delete operations change records only after approval of the exact change through a supported client."
kind: "ticket"
tags: ["feature:task-coordination", "feature:document-management", "feature:agent-role-management", "concern:authorization", "concern:auditability", "concern:data-integrity", "concern:security"]
---

# T-008 — Enforce verified client approval for agent mutations

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-003, T-004, T-005, T-006, T-007, T-018
Estimate (days): 3.5
Estimate scope: Build
Estimate basis: Provisional/high uncertainty: common approval state machine and negative tests/review; target-client mediation and verification are separate.

## Outcome
Agent Update/Delete operations change records only after approval of the exact change through a supported client.

## Acceptance Criteria
- Persist queryable mutation requests binding client, target, exact patch, payload hash, base revision, expiry and one-use decision; do not hold database transactions while waiting.
- Apply an accepted exact change with audit in one transaction; reject forged, replayed or stale approvals and do not expose an agent-callable approve shortcut.
- Leave unsupported-client requests pending/queryable with Needs approval; rejection, cancellation, timeout and disconnect do not mutate business records.
- Derive the badge independently of ticket status, clearing it only when no pending requests remain; test multiple requests, protected restores/deletes and planning-field updates.

## Context
- [US-012](../user-stories/US-012-approve-agent-updates-and-deletions-in-the-client.md)
- [approval-flow](../technical-architecture/approval-flow.md)
- [mcp-tools](../technical-architecture/mcp-tools.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-003](T-003-authorize-local-browser-and-agent-clients.md)
- [T-004](T-004-persist-tickets-and-progress.md)
- [T-005](T-005-persist-documents-and-bounded-revisions.md)
- [T-006](T-006-persist-ticket-document-links.md)
- [T-007](T-007-record-filter-and-expire-activity.md)
- [T-018](T-018-persist-ticket-classification-and-estimates.md)
