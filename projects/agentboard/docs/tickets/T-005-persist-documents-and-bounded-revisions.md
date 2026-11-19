---
name: "T-005 — Persist documents and bounded revision history"
description: "Document edits, comparisons and restores use Postgres with current content plus at most three previous versions."
kind: "ticket"
tags: ["feature:document-management", "concern:data-integrity", "concern:retention", "concern:privacy"]
---

# T-005 — Persist documents and bounded revision history

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-002, T-003
Estimate (days): 3
Estimate scope: Build
Estimate basis: Provisional: transactional versioning and comparison behavior with concurrency tests/review; FE editor wiring separate.

## Outcome
Document edits, comparisons and restores use Postgres with current content plus at most three previous versions.

## Acceptance Criteria
- Implement validated document CRUD and retained-version list/read/compare/restore routes with explicit unavailable-version results.
- Serialize competing edits/restores using revision checks; preserve outgoing content, create the new current version and prune in one transaction.
- Update timestamps only on successful changes; failed/unapproved writes create no version.
- Test concurrent edits, restore-as-new-version, pruning boundaries and document deletion of content/history; keep agent restore approval delegated to the shared gate.

## Context
- [US-007](../user-stories/US-007-maintain-project-documents.md)
- [US-015](../user-stories/US-015-read-compare-and-restore-document-revisions.md)
- [document-history](../technical-architecture/document-history.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [data-model](../technical-architecture/data-model.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-002](T-002-persist-projects-and-agent-roles.md)
- [T-003](T-003-authorize-local-browser-and-agent-clients.md)
