# Data Model

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## 5. Data & Storage Design


Server-generated UUIDs; UTC timestamps; mutable domain rows carry integer revision and created_at/updated_at. Project IDs constrain related records through composite foreign keys. Store document bodies as text in Postgres, not host Markdown files.

| Entity | Essential data and invariants |
| --- | --- |
| Project | Name, purpose; nonblank name; duplicate names distinguished by ID and visible creation detail |
| AgentRole | Project, name, responsibilities; role definitions do not imply a running process |
| Ticket | Project, title, description, priority, status, owner_kind, role_id, blocker_reason, revision |
| Document / DocumentVersion | Current content and version ID; previous content, version ID, author/source, timestamp; at most three previous versions per document |
| TicketDocument | Same-project ticket/document association; relationship context/output; unique tuple |
| AgentClient | Local credential identifier and declared client/agent label; client labels are attribution, not cryptographic proof of a human identity |
| MutationRequest | Target/project/ticket association, operation, exact proposed patch or deletion, base revision, payload hash, requester, status, creation/expiry/decision times |
| ActivityEvent | Server ID, deduplication key, project, optional ticket, agent/client, action/event_type, outcome, labels, occurred_at, received_at, provenance |

Ticket status remains Planned / In Progress / Blocked / Done. Approval is a separate indicator derived from one or more pending MutationRequests. A document or project mutation without a ticket stays visible on its record/activity; agents may supply a same-project ticket association. Never invent a ticket to attach a request.


Indexes: project/status, project/priority, document/project, activity received_at, project/ticket/agent/event_type/time, labels as suitable JSONB/GIN or normalized labels after measurement, and pending requests by ticket/status. Use row locks and revision checks for agent commits; no mutable progress counters. A successful operation and its automatic audit event commit together.


Related rules: [document history](document-history.md), [approval flow](approval-flow.md), and [activity logging](activity-logging.md).
