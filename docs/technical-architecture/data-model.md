---
name: "Data Model"
description: "Define records and database invariants. Policy details belong in the linked topic files."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:data-integrity", "concern:retention", "concern:auditability", "concern:security"]
---

# Data Model

> Owner: Solution Architect | Version: 0.1.4 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Define records and database invariants. Policy details belong in the linked topic files.

## Data & Storage Design

| Baseline | Rule |
| --- | --- |
| IDs / times | Server UUIDs; UTC timestamps |
| Mutable rows | Integer revision, `created_at`, `updated_at` |
| Project isolation | Composite project/record foreign keys |
| AgentBuild | Connected skill commands write records directly to AgentBoard; no local file watcher or shadow copy |
| Documents | Text and structured metadata in Postgres, not host Markdown files |

| Entity | Fields / invariant |
| --- | --- |
| Project | Name, purpose; nonblank name; duplicates distinguished by ID and visible creation detail |
| AgentRole | Project, name, responsibilities; no implied running process |
| Ticket | Project, source ID, title/summary/details, feature and concern tags, FE/BE execution role, BUG/BUILD type, verification, assignment, estimate/scope/basis, milestone, priority/status/owner/blocker, revision |
| Document / DocumentVersion | Title, summary, kind, tags, content, AgentBuild/upload provenance, version ID, author/source, timestamp; revisions preserve metadata; [retention rules](document-history.md) |
| ProjectTag | Project-scoped feature/concern ID, label, definition and source; validates artifact tags against the project vocabulary |
| ArtifactTag | Project-scoped association from a ticket or document to a ProjectTag; indexed for filters |
| TicketDocument | Same-project ticket/document; context/output relationship; unique tuple |
| AgentClient | Local credential ID and declared agent/client label; attribution is not verified human identity |
| MutationRequest | Target/project/optional ticket, operation, exact patch/deletion, base revision, payload hash, requester, status and lifecycle timestamps |
| ActivityEvent | Server ID, deduplication key, project/optional ticket, agent/client, action/type, outcome, labels, occurred/received times, provenance |

## Transaction Rules

1. Ticket status is **Planned / In Progress / Blocked / Done**. Pending mutation requests derive a separate **Needs approval** indicator.
2. Agent commits use row locks and revision checks. A successful operation and its automatic audit event commit together.
3. Progress is queried from current records; do not maintain mutable progress counters.
4. A project/document mutation without a ticket remains visible on that record/activity. Accept a same-project ticket association; never invent one.
5. AgentBuild-connected creates go directly to the app and return stable record IDs; retry keys prevent duplicate records. Local-only files are independent.
6. Imported files retain source filename and upload provenance. Extracted metadata is a suggestion until the user reviews and confirms it.

## Index Plan — Proposed

| Query | Index candidates |
| --- | --- |
| Ticket lists | Project/status; project/priority |
| Ticket/document tags | Project + namespace/tag ID + artifact ID |
| Documents | Project/kind; project/source reference |
| Activity / cleanup | `received_at`; project/ticket/agent/type/time |
| Labels | JSONB/GIN or normalized labels after measurement |
| Pending approvals | Ticket/status |

[Document history](document-history.md) · [Approval policy](approval-flow.md) · [Activity schema and expiry](activity-logging.md)

## Exact Fields and Record Examples

[Shared domain schema](contracts/schemas/domain.schema.json) defines types, required fields and allowed values.

- [TicketRecord example](examples/data/ticket.record.json): persisted state, without the derived approval badge.
- [MutationRequest example](examples/data/mutation-request.record.json): exact pending change and revision binding.
- [DocumentVersion example](examples/data/document-version.record.json): retained immutable content.

`TicketView` is a separate API/MCP projection with `needs_approval`. UI labels map to lowercase wire values; see [contract conventions](contracts/README.md). Schemas do not replace foreign-key, transaction, retention-count or cross-record tests.
