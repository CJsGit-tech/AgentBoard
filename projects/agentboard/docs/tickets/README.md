---
name: "AgentBoard — Engineering tickets"
description: "Indexes engineering tickets by role, type, estimate, and dependencies."
kind: "ticket-index"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:data-integrity", "concern:reliability"]
---

# AgentBoard — Engineering tickets

> Owner: Product Manager | Version: 0.1.4 | Status: draft | Last Updated: 2026-11-18

24 BUILD tickets (9 FE and 15 BE) and three BUG tickets (one FE and two BE). The status column records ticket closure. Current runtime evidence is tracked in the [review report](../review-report.md).

## Planning basis

The existing React/Vite screens were reused for the connected browser app. FastAPI and Postgres run through the checked-in Docker Compose configuration. Earlier visual approval covers the recorded mock screens. This backlog is stored in the project's confirmed file-only workspace. In connected mode, AgentBuild writes records directly to the AgentBoard app.

Estimates are provisional effort: one day = eight focused working hours for one assigned worker, including scoped tests/review. FE: **18.5 days**; BE: **36.5 days**; combined **55 effort-days**, not elapsed time or an agent runtime promise. Dependency waits, available capacity and client capability uncertainty prevent a reliable completion date. Advanced timeline scheduling is excluded until its policy is confirmed in T-018/T-019; those estimates cover the stated baseline only.

FE → Frontend Programmer; BE → Backend Programmer. Work type is separate from role and ownership. Engineering ticket status uses the skill workflow; the app's Planned/In Progress/Blocked/Done contract remains unchanged. Needs approval stays separate. Detailed claims require actual execution evidence; no implementation starts with this planning command.

## Tickets

| ID / title | Role | Type | Status | Verification | Estimate (days) | Scope |
| --- | --- | --- | --- | --- | ---: | --- |
| [T-001 — Establish FastAPI and Postgres foundation](T-001-establish-backend-and-database.md) | BE | BUILD | Open | Not applicable | 2 | Build |
| [T-002 — Persist projects and agent roles through REST](T-002-persist-projects-and-agent-roles.md) | BE | BUILD | Open | Not applicable | 2 | Build |
| [T-003 — Authorize local browser and agent clients](T-003-authorize-local-browser-and-agent-clients.md) | BE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-004 — Persist tickets, responsibility and progress](T-004-persist-tickets-and-progress.md) | BE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-005 — Persist documents and bounded revision history](T-005-persist-documents-and-bounded-revisions.md) | BE | BUILD | Open | Not applicable | 3 | Build |
| [T-006 — Persist ticket context and output links](T-006-persist-ticket-document-links.md) | BE | BUILD | Open | Not applicable | 1 | Build |
| [T-007 — Record, filter and expire activity after 30 days](T-007-record-filter-and-expire-activity.md) | BE | BUILD | Open | Not applicable | 3 | Build |
| [T-008 — Enforce verified client approval for agent mutations](T-008-enforce-client-approved-mutations.md) | BE | BUILD | Open | Not applicable | 3.5 | Build |
| [T-009 — Expose shared services as typed MCP tools](T-009-expose-typed-mcp-tools.md) | BE | BUILD | Open | Not applicable | 3 | Build |
| [T-010 — Verify Codex and Claude MCP client workflows](T-010-verify-codex-and-claude-client-workflows.md) | BE | BUILD | In progress | Not applicable | 3 | Build |
| [T-011 — Stream committed project events with safe reconnect](T-011-stream-committed-project-events.md) | BE | BUILD | Open | Not applicable | 2 | Build |
| [T-012 — Package local Compose deployment and recovery](T-012-package-local-compose-and-recovery.md) | BE | BUILD | Open | Not applicable | 3 | Build |
| [T-013 — Connect frontend data access to authenticated REST](T-013-connect-frontend-to-authenticated-api.md) | FE | BUILD | Open | Not applicable | 2 | Build |
| [T-014 — Connect project and role screens to persistence](T-014-connect-project-and-role-screens.md) | FE | BUILD | Open | Not applicable | 1.5 | Build |
| [T-015 — Connect ticket board, document links and progress](T-015-connect-ticket-board-and-progress.md) | FE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-016 — Connect document editor and revision history](T-016-connect-document-editor-and-history.md) | FE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-017 — Connect live activity and approval request displays](T-017-connect-live-activity-and-approval-badges.md) | FE | BUILD | Open | Not applicable | 2 | Build |
| [T-018 — Persist ticket classification, estimates and planning data](T-018-persist-ticket-classification-and-estimates.md) | BE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-019 — Show ticket classifications, estimates and timeline context](T-019-show-ticket-estimates-and-planning-context.md) | FE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-020 — Verify complete persisted desktop user journeys](T-020-verify-persisted-desktop-user-journeys.md) | FE | BUILD | In progress | Not applicable | 2 | Build |
| [T-021 — Persist and filter project artifact tags](T-021-persist-and-filter-artifact-tags.md) | BE | BUILD | Open | Not applicable | 2 | Build |
| [T-022 — Filter project artifacts by tags](T-022-filter-project-artifacts-by-tags.md) | FE | BUILD | Open | Not applicable | 1.5 | Build |
| [T-023 — Persist reviewed document uploads and provenance](T-023-persist-reviewed-document-uploads.md) | BE | BUILD | Open | Not applicable | 1.5 | Build |
| [T-024 — Upload documents with metadata](T-024-upload-documents-with-metadata.md) | FE | BUILD | Open | Not applicable | 2 | Build |
| [T-025 — Resync timezone-free activity cursors](T-025-resync-timezone-free-activity-cursors.md) | BE | BUG | Done | Fixed | 0.25 | Repair |
| [T-026 — Keep keyboard focus inside controls](T-026-keep-keyboard-focus-inside-controls.md) | FE | BUG | Done | Fixed | 0.25 | Repair |
| [T-027 — Require verified client approval](T-027-require-verified-client-approval.md) | BE | BUG | Done | Fixed | 1 | Repair |

## Start here

Use the [run guide](../../README.md) for the connected app and the [review report](../review-report.md) for current verification. T-010 records remaining MCP client compatibility work. The table keeps each ticket’s closure tied to its own acceptance evidence.

## Coverage

| Existing story scope | BE tickets | FE tickets |
| --- | --- | --- |
| US-001–003 Projects/roles | T-002 | T-014 |
| US-004–006, US-009 Tickets/progress | T-004 | T-015 |
| US-007, US-015 Documents/revisions | T-005 | T-016 |
| US-008 Context/output links | T-006 | T-015 |
| US-010, US-013–014 Activity/retention | T-007, T-011 | T-017 |
| US-011–012 MCP/approval | T-003, T-008–010 | T-017 |
| New classification/estimates/timeline brief | T-018 | T-019 |
| US-016 Project artifact tag filters | T-021 | T-022 |
| US-017 Reviewed Markdown upload with metadata | T-023 | T-024 |
| Shared foundation/delivery/end-to-end | T-001, T-012 | T-013, T-020 |

[Stories](../user-stories/README.md) · [Architecture](../technical-architecture/README.md) · [Approved screens](../designs/screens/README.md)
