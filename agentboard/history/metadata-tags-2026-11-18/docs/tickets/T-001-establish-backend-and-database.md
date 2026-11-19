# T-001 — Establish FastAPI and Postgres foundation

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: None
Estimate (days): 2
Estimate scope: Build
Estimate basis: Provisional: new backend scaffolding and base migrations plus integration tests/review; feature behavior is estimated separately.

## Outcome
A runnable backend can connect to Postgres, apply migrations and commit domain changes with audit events.

## Acceptance Criteria
- Create the planned backend layout, validated settings, readiness endpoints and pinned/tested Python dependencies; record selected versions rather than claiming untested compatibility.
- Add Alembic migrations for the documented domain, project-scoped constraints, revisions and timestamps; align actual schemas with the draft contract before downstream work.
- Provide transaction/audit helpers and deterministic integration-test database setup; rollback failed mutations and their success events together.
- Demonstrate migration from an empty database, restart persistence and explicit database-unavailable readiness behavior.

## Context
- [source-layout](../technical-architecture/source-layout.md)
- [data-model](../technical-architecture/data-model.md)
- [technology-stack](../technical-architecture/technology-stack.md)
- [Assigned role](../../agents/backend-programmer.md)
