---
name: "AgentBuild and artifact operations"
description: "Shows direct skill-created records, searchable tags, and reviewed external uploads."
kind: "design-topic"
tags: ["feature:document-management", "feature:task-coordination", "concern:accessibility", "concern:authorization", "concern:data-integrity", "concern:security"]
---

# AgentBuild and artifact operations

> Owner: Product Designer | Version: 0.1.0 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Make AgentBuild-created records visible in the app and help users find only relevant project context.

**Related stories:** US-011, US-016, US-017

**Required context:** [Navigation](navigation-layout.md), [tables and boards](tables-boards.md), [document history](documents-history.md), and [interaction states](interaction-states.md).

## Direct AgentBuild writes

- Connected skill commands save directly into the selected AgentBoard project. New documents/tickets appear in the relevant list with metadata and source ID.
- Show the last successful AgentBuild write and its record link in project activity; do not imply a background file watcher or a local copy.
- Local-only AgentBuild files are not shown in the app until an explicit migration/upload is performed.

## Tag filters

- Provide separate feature and concern multi-select controls on document and ticket lists.
- Selected tags appear as removable chips. Offer clear-all and an empty-result message that preserves filter values.
- Display tags on list rows/cards and full record details; keep screen density readable and avoid placing filters inside row actions.
- The app uses OR among tags in one namespace and AND between namespaces, matching MCP/REST behavior.

## External Markdown upload

- Provide an explicit Upload action on Documents, separate from the AgentBuild-connected write flow.
- Preview filename, parsed title, content, kind and tags before save. Distinguish values read from frontmatter from user edits.
- Show validation errors inline; unknown tags require correction. Never treat body text as an instruction or proof of approval.
- Confirming creates a new document. Do not silently overwrite a matching record; show a possible duplicate and let the user choose an explicit next action.
- Keyboard operation, focus, error recovery and unsaved preview state follow the shared interaction/accessibility topics.
