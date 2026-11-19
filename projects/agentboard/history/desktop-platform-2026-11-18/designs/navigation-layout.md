# Navigation and layout

> Owner: Product Designer | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Keep project context visible while users inspect and operate on records.

**Related stories:** Cross-cutting

**Required context:** [Interaction states](interaction-states.md) and [accessibility](accessibility.md).

## Navigation

Project picker → Overview, Tickets (Table / Board), Roles, Documents, Activity. Roles describe responsibilities, not running agents. Support project/record deep links and missing-record states. No launch controls, global search or connection manager is specified.

| Width | Layout |
| --- | --- |
| ≥1280px | 216px sidebar; fluid content; optional 440px inspector |
| 960–1279px | 200px sidebar; details overlay |
| 768–959px | Collapsible navigation; single content region |
| <768px | Full-width details; labeled table rows; selectable board status column |

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
