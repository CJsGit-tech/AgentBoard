---
name: "T-021 — Persist and filter project artifact tags"
description: "Documents and tickets use validated project tags with matching REST and MCP filters."
kind: "ticket"
tags: ["feature:document-management", "feature:task-coordination", "concern:data-integrity", "concern:compatibility"]
---

# T-021 — Persist and filter project artifact tags

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-004, T-005, T-009, T-018
Estimate (days): 2
Estimate scope: Build
Estimate basis: Provisional: vocabulary validation, project-scoped queries, REST/MCP parity, migrations and contract updates.

## Outcome
Project documents and tickets can be filtered by validated feature and concern tags through both the browser API and MCP.

## Acceptance Criteria
- Reconcile current prose claims with the OpenAPI, MCP catalog, schemas, examples and domain model before implementation; document canonical query names, validation errors, pagination and tag storage consistently.
- Store zero or more valid feature/concern tags for each document and ticket; reject malformed, unknown, or wrong-namespace tags with a clear validation error.
- Support project-scoped document and ticket filtering: OR within each nonempty namespace and AND across nonempty namespaces; omitted filters do not filter.
- Return the same records, stable pagination and ordering semantics from REST and MCP for equivalent filters.
- Add migration/default behavior for existing records and verify that untagged records remain readable and listable.

## Context
- [US-016](../user-stories/US-016-filter-project-artifacts-by-tags.md)
- [Tag vocabulary](../tag-vocabulary.md)
- [API contracts](../technical-architecture/api-contracts.md)
- [MCP tools](../technical-architecture/mcp-tools.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-004](T-004-persist-tickets-and-progress.md)
- [T-005](T-005-persist-documents-and-bounded-revisions.md)
- [T-009](T-009-expose-typed-mcp-tools.md)
- [T-018](T-018-persist-ticket-classification-and-estimates.md)
