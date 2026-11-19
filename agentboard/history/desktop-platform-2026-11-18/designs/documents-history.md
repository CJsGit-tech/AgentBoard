# Documents and history

> Owner: Product Designer | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Read, compare and rework documents without loading every revision.

**Related stories:** US-007, US-008, US-015

**Required context:** [Interaction states](interaction-states.md) and [accessibility](accessibility.md). See [approval states](approval-states.md).

- Start with title list; open selected content with an outline. Load history and comparisons on demand.
- Preserve current content and at most three previous versions. Show updated time and revision identity. Explain when a requested revision has been pruned.
- Agents can read retained revisions and rework content. An agent restore is an Update and requires client approval.
- Compare revisions with labeled additions/deletions. Retain a draft on conflict and display newer canonical content.
- Restore/delete explains impact and requires explicit user action. The web interface does not add a second approval gate to a client-approved request.
- The outline is a human reading aid; it does not introduce an MCP section API or import feature.
- Link relevant outputs; do not imply arbitrary full tool payload storage.

Document content and history live in Postgres. These UI rules do not extend the [existing contracts](../technical-architecture/contracts/README.md).
