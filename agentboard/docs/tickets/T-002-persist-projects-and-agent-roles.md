---
name: "T-002 — Persist projects and agent roles through REST"
description: "Projects and responsibility definitions survive reloads and remain isolated by project."
kind: "ticket"
tags: ["feature:product-project-management", "feature:agent-role-management", "concern:data-integrity", "concern:security"]
---

# T-002 — Persist projects and agent roles through REST

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-001, T-003
Estimate (days): 2
Estimate scope: Build
Estimate basis: Provisional: shared foundation/auth reused; resource handlers, service tests and review included.

## Outcome
Projects and responsibility definitions survive reloads and remain isolated by project.

## Acceptance Criteria
- Implement documented list/read/create/update/delete operations for projects and roles with validation, pagination and stable identifiers.
- Return actionable validation/save errors; changing project/role details preserves related records and assignments.
- Reject deletion of an assigned role or nonempty project; do not silently cascade.
- Test duplicate project-name distinction, cross-project access, stale revisions and atomic mutation/audit behavior.

## Context
- [US-001](../user-stories/US-001-create-a-product-project.md)
- [US-002](../user-stories/US-002-find-and-switch-projects.md)
- [US-003](../user-stories/US-003-define-project-agent-roles.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [data-model](../technical-architecture/data-model.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-001](T-001-establish-backend-and-database.md)
- [T-003](T-003-authorize-local-browser-and-agent-clients.md)
