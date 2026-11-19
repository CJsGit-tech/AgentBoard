---
name: "Navigation and layout"
description: "Keep project context visible while users inspect and operate on records."
kind: "design-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:accessibility", "concern:reliability"]
---

# Navigation and layout

> Owner: Product Designer | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Keep project context visible while users inspect and operate on records.

**Related stories:** Cross-cutting

**Required context:** [Interaction states](interaction-states.md) and [accessibility](accessibility.md).

## Navigation

Project picker → Overview, Tickets (Table / Board), Roles, Documents, Activity. Roles describe responsibilities, not running agents. Support project/record deep links and missing-record states. No launch controls, global search or connection manager is specified.

**Confirmed environment:** desktop browser on the owner's personal computer; local Docker Compose, one user, keyboard and pointer. No phone or native iOS deliverable. See [deployment constraints](../technical-architecture/constraints.md).

| Proposed browser width | Layout |
| --- | --- |
| ≥1440px | Full sidebar, work surface and persistent inspector |
| 1100–1439px | Sidebar and work surface; inspector overlays when open |
| 800–1099px | Compact navigation; scrollable native table/board; inspector overlays |
| <800px or high zoom | Compact desktop fallback; horizontal work-surface scrolling; details fit available width |

Responsiveness preserves desktop operations during window resizing, zoom and content growth. It does not introduce phone navigation or touch layouts. Validate 1600×1100, 1280×900 and 900×900 as proposed review sizes; exact minimum window size and supported browsers await confirmation.

Keep project/page identity, one primary action and dominant work surface. Preserve filters, scroll and draft values when opening details. Preview only relevant context; expand details on demand.

## Screen coverage

| Route under /projects/:p | Stories |
| --- | --- |
| Overview | US-009, US-012 |
| Tickets and ticket details | US-004, US-005, US-006, US-008, US-010, US-012 |
| Roles | US-003, US-005 |
| Documents and details | US-007, US-008, US-015 |
| Activity | US-010, US-011, US-013, US-014 |

`/projects` supports US-001 and US-002. All route names and responsive dimensions are proposed.

## Approved screen reference

Use the [screen inventory and component map](screens/README.md) to find the approved frontend source and captures for each route. Approval recorded on 2026-11-18; production integrations remain outside this screen deliverable.
