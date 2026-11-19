# Data Model

> Owner: Solution Architect | Version: 0.1.3 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Define records and database invariants. Policy details belong in the linked topic files.

## Data & Storage Design

| Baseline | Rule |
| --- | --- |
| IDs / times | Server UUIDs; UTC timestamps |
| Mutable rows | Integer revision, `created_at`, `updated_at` |
| Project isolation | Composite project/record foreign keys |
| Documents | Text in Postgres, not host Markdown files |

| Entity | Fields / invariant |
| --- | --- |
| Project | Name, purpose; nonblank name; duplicates distinguished by ID and visible creation detail |
| AgentRole | Project, name, responsibilities; no implied running process |
| Ticket | Project, title, description, priority, status, owner kind, role ID, blocker reason, revision |
| Document / DocumentVersion | Current/history content, version ID, author/source, timestamp; [retention rules](document-history.md) |
| TicketDocument | Same-project ticket/document; context/output relationship; unique tuple |
| AgentClient | Local credential ID and declared agent/client label; attribution is not verified human identity |
| MutationRequest | Target/project/optional ticket, operation, exact patch/deletion, base revision, payload hash, requester, status and lifecycle timestamps |
| ActivityEvent | Server ID, deduplication key, project/optional ticket, agent/client, action/type, outcome, labels, occurred/received times, provenance |

## Transaction Rules

1. Ticket status is **Planned / In Progress / Blocked / Done**. Pending mutation requests derive a separate **Needs approval** indicator.
2. Agent commits use row locks and revision checks. A successful operation and its automatic audit event commit together.
3. Progress is queried from current records; do not maintain mutable progress counters.
4. A project/document mutation without a ticket remains visible on that record/activity. Accept a same-project ticket association; never invent one.

## Index Plan — Proposed

| Query | Index candidates |
| --- | --- |
| Ticket lists | Project/status; project/priority |
| Documents | Project |
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
