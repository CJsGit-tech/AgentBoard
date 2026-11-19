---
name: "Tickets, tables and boards"
description: "Inspect and operate on tickets with stable context."
kind: "design-topic"
tags: ["feature:task-coordination", "feature:agent-role-management", "feature:progress-tracking", "concern:authorization", "concern:accessibility", "concern:data-integrity"]
---

# Tickets, tables and boards

> Owner: Product Designer | Version: 0.1.3 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Inspect and operate on tickets with stable context.

**Related stories:** US-004, US-005, US-006

**Required context:** [Interaction states](interaction-states.md) and [accessibility](accessibility.md).

- Default to a table; offer a board using the same records and actions. Table columns: title, status, owner, priority, approval badge and updated time. Rows start at 44px and grow for content.
- Offer separate feature-tag and concern-tag filters. Multiple selections within one tag family use OR; active filters across families use AND. Show selected tags as removable chips and provide a clear-all action.
- Ticket detail exposes FE/BE execution role, BUG/BUILD type, verification, estimate in days and estimate scope; these fields never become board status values.
- Open a right inspector without losing filters or scroll. Show summary first, then description, blockers, links, activity and request differences.
- Board has exactly Planned, In progress, Blocked and Done columns. Needs approval remains a separate badge, never a status column.
- Cards show title, owner, priority, time and approval; preview two title lines with full text on opening.
- Paginate each column independently; show count context and Load more. Never present the first page as all records.
- Use labeled fields, required indicators, explicit Save and unsaved warning. Gate Blocked with a reason. Handle unassigned owners and duplicate/failed saves explicitly.
- Store table/board preference locally; business records remain in Postgres.

## Unresolved contract

Architect: global priority sorting across pagination is not in current OpenAPI. Define its contract before implementing; sorting only visible rows is misleading.
