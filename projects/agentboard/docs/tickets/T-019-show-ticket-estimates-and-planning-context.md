---
name: "T-019 — Show ticket classifications, estimates and timeline context"
description: "The board makes FE/BE, BUG/BUILD and estimated effort visible without pretending estimates are delivery dates."
kind: "ticket"
tags: ["feature:task-coordination", "feature:progress-tracking", "concern:accessibility", "concern:data-integrity", "concern:reliability"]
---

# T-019 — Show ticket classifications, estimates and timeline context

Role: FE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-015, T-018
Estimate (days): 2.5
Estimate scope: Build
Estimate basis: Provisional/high uncertainty: modest extension of approved screens and integration tests/review; timeline visualization/policy may change scope after design confirmation.

## Outcome
The board makes FE/BE, BUG/BUILD and estimated effort visible without pretending estimates are delivery dates.

## Acceptance Criteria
- Extend existing editor/table/board/detail components with the agreed classification and estimate fields; support filtering without duplicating the frontend.
- Show estimate scope/basis and distinguish investigation-only estimates from unknown repair; retain values across saves and reloads.
- Propose the smallest timeline presentation consistent with the planning contract and obtain design confirmation before adding date controls or schedule visualizations.
- Display available planning inputs and explicit unknown forecast states; do not sum parallel FE/BE effort into a promised calendar deadline.
- Refresh affected design guidance and screen evidence after authorized implementation; test validation/failure, filtering, resized desktop windows and inset focus/padded icons.

## Context
- Latest user decisions in this conversation (2026-11-18): FE/BE routing, BUG/BUILD classification, per-ticket estimates in days, and AgentBoard timeline/estimate tracking. Existing schemas/screens do not yet cover this extension; detailed scheduling behavior remains to be confirmed.
- [api-contracts](../technical-architecture/api-contracts.md)
- [Approved screen inventory](../designs/screens/README.md)
- [Existing implementation](../../frontend/src/features/tickets/TicketEditor.tsx)
- [Assigned role](../../agents/frontend-programmer.md)

## Dependencies
- [T-015](T-015-connect-ticket-board-and-progress.md)
- [T-018](T-018-persist-ticket-classification-and-estimates.md)
