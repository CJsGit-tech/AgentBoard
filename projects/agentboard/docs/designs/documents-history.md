---
name: "Documents and history"
description: "Read, compare and rework documents without loading every revision."
kind: "design-topic"
tags: ["feature:document-management", "feature:task-coordination", "concern:data-integrity", "concern:retention", "concern:authorization", "concern:privacy"]
---

# Documents and history

> Owner: Product Designer | Version: 0.1.4 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Read, compare and rework documents without loading every revision.

**Related stories:** US-007, US-008, US-015

**Required context:** [Interaction states](interaction-states.md) and [accessibility](accessibility.md). See [approval states](approval-states.md).

- Start with title list; open selected content with an outline. Load history and comparisons on demand.
- Show document kind and feature/concern tags in the list and detail header; tag filters narrow the list without loading unrelated content.
- AgentBuild-generated documents appear directly in the shared AgentBoard project. External Markdown uploads use a preview that labels extracted metadata before saving.
- Preserve current content and at most three previous versions. Show updated time and revision identity. Explain when a requested revision has been pruned.
- Agents can read retained revisions and rework content. An agent restore is an Update and requires client approval.
- Compare revisions with labeled additions/deletions. Retain a draft on conflict and display newer canonical content.
- Restore/delete explains impact and requires explicit user action. The web interface does not add a second approval gate to a client-approved request.
- The outline is a human reading aid; it does not introduce an MCP section API.
- Link relevant outputs; do not imply arbitrary full tool payload storage.

Document content and history live in Postgres. These UI rules do not extend the [existing contracts](../technical-architecture/contracts/README.md).
