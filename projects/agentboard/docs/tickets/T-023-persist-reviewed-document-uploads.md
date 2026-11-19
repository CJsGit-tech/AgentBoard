---
name: "T-023 — Persist reviewed document uploads and provenance"
description: "Confirmed Markdown uploads create canonical documents with validated metadata and source provenance."
kind: "ticket"
tags: ["feature:document-management", "concern:data-integrity", "concern:auditability", "concern:security"]
---

# T-023 — Persist reviewed document uploads and provenance

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-005, T-021
Estimate (days): 1.5
Estimate scope: Build
Estimate basis: Provisional: document write contract, provenance fields, validation and source-preservation checks.

## Outcome
After user confirmation, a supported Markdown upload is stored as a canonical project document with its original content, reviewed metadata and upload provenance.

## Acceptance Criteria
- Reconcile upload claims in API prose against OpenAPI, MCP catalog, schemas, examples and document model before implementation; define whether preview parsing is client-side and the exact confirmed-create request.
- Accept only the confirmed Markdown content and metadata; validate tags against the project's vocabulary and enforce the existing document size limit.
- Persist original Markdown content, source filename, upload time and metadata provenance without treating file content as instructions, approval, owner, or workflow state.
- Create through the same project authorization, idempotency, audit, and activity rules as other document creation; preserve direct AgentBuild document creation as a separate supported path.
- Reject invalid or unsupported inputs without creating partial documents and return field-level errors.

## Context
- [US-017](../user-stories/US-017-upload-documents-with-metadata.md)
- [AgentBuild integration](../technical-architecture/agentbuild-integration.md)
- [API contracts](../technical-architecture/api-contracts.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-005](T-005-persist-documents-and-bounded-revisions.md)
- [T-021](T-021-persist-and-filter-artifact-tags.md)
