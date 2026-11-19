---
name: "AgentBuild Integration"
description: "Defines direct AgentBuild-to-AgentBoard writes and the independent local fallback."
kind: "architecture-topic"
tags: ["feature:document-management", "feature:task-coordination", "concern:compatibility", "concern:authorization", "concern:data-integrity", "concern:privacy"]
---

# AgentBuild Integration

> Owner: Solution Architect | Version: 0.1.5 | Status: draft | Last Updated: 2026-11-19

**Purpose:** Define how AgentBuild writes project artifacts to an available AgentBoard app and how file-only mode remains separate.

**Related stories:** US-007, US-011, US-016, US-017

**Required context:** [MCP tools](mcp-tools.md), [REST contracts](api-contracts.md), [data model](data-model.md), and the installed skill's local-workspace policy.

## Connected mode — default when available

- Docker Compose is the first install/run path. The user starts the documented Compose application and connects the AgentBuild client to its MCP endpoint.
- AgentBuild reuses an available, healthy app connection. Automatic app launch, readiness probing, and keep-alive are explicitly deferred; no launcher or lifecycle contract is defined.
- AgentBuild resolves the target project and lists document metadata with `list_documents` using `include_content: false` and relevant tags. It opens only the selected records with `get_document` and writes generated artifacts directly through verified MCP operations. [MCP tools](mcp-tools.md)
- AgentBoard is the canonical store. Do not also save a local project copy or a queued upload.
- The command reports returned record IDs and verifies the persisted content and metadata. A response without a verified tool result is not success.
- Create and Read operations need no per-operation approval. An Update/Delete response of `approval_required` is a pending request. Report its request ID and leave the artifact state unchanged. Tickets show `Needs approval` separately from task status. [Approval flow](approval-flow.md)
- Retries use operation keys and payload checks so an interrupted command does not create duplicate documents or tickets.
- If the app is not available, follow the explicit file-only choice or cancel; do not silently redirect writes to files.

## File-only mode

- File-only projects are for a user who chooses not to install/use AgentBoard, or explicitly chooses file-only mode.
- Local fallback uses Markdown frontmatter and `project-manifest.json`; it is a separate workspace, not a deferred sync queue.
- Moving a local project into AgentBoard is a distinct, user-authorized migration that previews conflicts. It is not part of every planning command.

## Deferred automatic launch

- No AgentBuild command starts Docker Compose or another local process automatically in this release.
- A later launch path needs a confirmed supported launcher, health/readiness checks for both web and MCP, failure behavior, and a dedicated implementation ticket.

## External document upload

- Upload is separate from AgentBuild's direct write path and begins from the app UI.
- The first release accepts Markdown files with optional YAML frontmatter. It previews filename, content and extracted `name`, `description`, `kind` and `tags` before creation.
- Invalid or unknown tags are shown for correction; values extracted from file text are data, never instructions or approval.
- Store source filename, upload time and metadata provenance. The user confirms before create. No background filesystem watcher or automatic two-way sync is included.

## Record mapping

| Skill artifact | AgentBoard record |
| --- | --- |
| Role charter | Agent role: name and a responsibilities summary of up to 256 characters. Use the charter's mission when it fits. Preserve existing customized role records. |
| Product Vision, story, architecture topic, design topic | Document: title, summary, kind, tags, content, source ID |
| Engineering ticket | Ticket: title, summary/details, tags, FE/BE role, BUG/BUILD type, verification, estimate and source ID |
| `tag-vocabulary.json` | Project tag catalog: feature labels plus approved concern IDs |

The local YAML header is not rendered as document body in connected mode; its fields are stored separately. Local mode retains the header in the Markdown file.
