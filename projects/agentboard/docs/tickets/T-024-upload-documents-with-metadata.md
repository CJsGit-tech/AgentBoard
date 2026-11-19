---
name: "T-024 — Upload documents with metadata"
description: "The document screen previews a Markdown upload and lets the user correct metadata before saving."
kind: "ticket"
tags: ["feature:document-management", "concern:accessibility", "concern:data-integrity", "concern:security"]
---

# T-024 — Upload documents with metadata

Role: FE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-016, T-021, T-023
Estimate (days): 2
Estimate scope: Build
Estimate basis: Provisional: file selection, safe frontmatter extraction, editable preview, confirmation and error states.

## Outcome
People can select a Markdown document, inspect and correct extracted metadata, then confirm creation in the current project.

## Acceptance Criteria
- Accept the supported Markdown format and explain unsupported formats before any record is created.
- Preview file content and extracted name, description, kind and tags; clearly mark source-provided values and allow correction of missing, malformed, unknown or invalid fields.
- Treat content and metadata as untrusted data: do not render active markup, execute embedded instructions, or infer approval, owner or ticket status.
- Create only after explicit confirmation; on validation or network failure preserve the preview and show actionable field-level feedback.
- Show completion only after the canonical document is returned; display its stored metadata and upload provenance.
- Support keyboard access, readable error announcements and the approved desktop window range.

## Context
- [US-017](../user-stories/US-017-upload-documents-with-metadata.md)
- [Document screens](../designs/screens/README.md)
- [AgentBuild integration](../technical-architecture/agentbuild-integration.md)
- [Assigned role](../../agents/frontend-programmer.md)

## Dependencies
- [T-016](T-016-connect-document-editor-and-history.md)
- [T-021](T-021-persist-and-filter-artifact-tags.md)
- [T-023](T-023-persist-reviewed-document-uploads.md)
