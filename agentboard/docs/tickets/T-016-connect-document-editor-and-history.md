---
name: "T-016 — Connect document editor and revision history"
description: "Existing document screens edit, compare and restore real retained revisions without losing drafts."
kind: "ticket"
tags: ["feature:document-management", "concern:data-integrity", "concern:retention", "concern:authorization", "concern:accessibility"]
---

# T-016 — Connect document editor and revision history

Role: FE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-005, T-013
Estimate (days): 2.5
Estimate scope: Build
Estimate basis: Provisional: existing document components reused; API wiring and browser regression checks/review.

## Outcome
Existing document screens edit, compare and restore real retained revisions without losing drafts.

## Acceptance Criteria
- Wire list/reader/editor/history/comparison/restore to the production adapter, using canonical revision IDs and saved timestamps.
- Handle conflicts, failed saves and missing/pruned versions explicitly; preserve edits through failed save and leave/back navigation guards.
- Display current plus up to three previous versions; restore creates a new current version, never substitutes an unavailable one.
- Save targeted browser evidence for save/reload, comparison, restore, pruning, conflict recovery and validation; keep safe content rendering.

## Context
- [US-007](../user-stories/US-007-maintain-project-documents.md)
- [US-015](../user-stories/US-015-read-compare-and-restore-document-revisions.md)
- [document-history](../technical-architecture/document-history.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [Approved screen inventory](../designs/screens/README.md)
- [Existing implementation](../../frontend/src/features/documents/DocumentHistoryScreen.tsx)
- [Assigned role](../../agents/frontend-programmer.md)

## Dependencies
- [T-005](T-005-persist-documents-and-bounded-revisions.md)
- [T-013](T-013-connect-frontend-to-authenticated-api.md)
