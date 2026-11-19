---
name: "Document History"
description: "Define agent-readable document history, comparison and restoration."
kind: "architecture-topic"
tags: ["feature:document-management", "feature:task-coordination", "concern:data-integrity", "concern:retention", "concern:authorization"]
---

# Document History

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Define agent-readable document history, comparison and restoration.

## Rules

- Retain the **current version + three most recent previous versions** in Postgres.
- You and authenticated agents can read and compare retained content; comparison is read-only.
- Update the document timestamp only after a successful content change.
- No hidden unbounded archive. Deleting a document removes its bodies and versions together; only minimal bounded audit metadata remains.

## Edit and Restore

```text
Check/lock current revision → Preserve outgoing content → Save new current
                                                        ↓
                                         Keep newest three previous versions
                    All steps commit in one transaction
```

| Action | Behavior |
| --- | --- |
| Edit | Create a new current version using the transaction above |
| Restore retained content | Copy it into a new current version; apply the same retention limit |
| Agent restore | Requires [client approval](approval-flow.md) |
| Failed/unapproved update | No new content version or updated timestamp |
| Requested version was pruned | Return unavailable; never substitute a different revision |

**Related:** [US-007](../user-stories/US-007-maintain-project-documents.md) · [US-015](../user-stories/US-015-read-compare-and-restore-document-revisions.md) · [MCP tools](mcp-tools.md) · [Backup distinction](deployment-operations.md)
