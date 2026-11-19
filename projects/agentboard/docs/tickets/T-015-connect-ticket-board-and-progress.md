---
name: "T-015 — Connect ticket board, document links and progress"
description: "Ticket table/board, ownership, blockers, links and overview reflect persisted records."
kind: "ticket"
tags: ["feature:task-coordination", "feature:progress-tracking", "feature:document-management", "concern:accessibility", "concern:data-integrity", "concern:authorization"]
---

# T-015 — Connect ticket board, document links and progress

Role: FE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-004, T-006, T-013
Estimate (days): 2.5
Estimate scope: Build
Estimate basis: Provisional: existing ticket/overview UI reused; integration and targeted tests/review; planning UI is separate.

## Outcome
Ticket table/board, ownership, blockers, links and overview reflect persisted records.

## Acceptance Criteria
- Wire existing ticket create/edit/status/priority/ownership controls and project-scoped filters to canonical REST responses.
- Persist Context/Output links without duplicates and maintain document/task return paths; handle unlink errors without deleting documents.
- Refetch accurate progress/blocker counts after successful saves; failed writes retain committed state and recoverable drafts.
- Test reload persistence, cross-project switches, stale revisions, reassignment/unassigned cases and table/board consistency; keep approval badge separate from status.

## Context
- [US-004](../user-stories/US-004-create-and-prioritize-tasks.md)
- [US-005](../user-stories/US-005-assign-task-responsibility.md)
- [US-006](../user-stories/US-006-track-task-progress-and-blockers.md)
- [US-008](../user-stories/US-008-connect-documents-and-task-outputs.md)
- [US-009](../user-stories/US-009-review-project-progress.md)
- [US-010](../user-stories/US-010-review-a-task-s-changes.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [approval-flow](../technical-architecture/approval-flow.md)
- [Approved screen inventory](../designs/screens/README.md)
- [Existing implementation](../../frontend/src/features/tickets/TicketsScreen.tsx)
- [Assigned role](../../agents/frontend-programmer.md)

## Dependencies
- [T-004](T-004-persist-tickets-and-progress.md)
- [T-006](T-006-persist-ticket-document-links.md)
- [T-013](T-013-connect-frontend-to-authenticated-api.md)
