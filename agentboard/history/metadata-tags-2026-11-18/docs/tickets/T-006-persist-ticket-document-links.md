# T-006 — Persist ticket context and output links

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-004, T-005
Estimate (days): 1
Estimate scope: Build
Estimate basis: Provisional: small association service on existing entities, API tests and review.

## Outcome
Tickets can link supporting documents and outputs without duplicate or cross-project associations.

## Acceptance Criteria
- Implement association list/create/delete using the documented Context/Output relationship mapping.
- Enforce same-project ticket/document constraints and uniqueness; repeated identical creates do not duplicate links.
- Removing an association preserves the document; record successful change audit atomically.
- Test missing/cross-project targets, retried creates and unlink behavior; agent removals use protected mutation authorization.

## Context
- [US-008](../user-stories/US-008-connect-documents-and-task-outputs.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [data-model](../technical-architecture/data-model.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-004](T-004-persist-tickets-and-progress.md)
- [T-005](T-005-persist-documents-and-bounded-revisions.md)
