---
name: "AgentBoard — Engineering tickets"
description: "Indexes 20 open BUILD tickets by role, type, estimate, and dependencies."
kind: "ticket-index"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:data-integrity", "concern:reliability"]
---

# AgentBoard — Engineering tickets

> Owner: Product Manager | Version: 0.1.0 | Status: draft | Last Updated: 2026-11-18

20 BUILD tickets; 7 FE and 13 BE. No unresolved bug report was supplied or independently verified in this planning run, so no BUG tickets were invented. All tickets are Open; dependencies determine readiness.

## Planning basis

Existing React/Vite screens and mock behaviors are approved; reuse them. There is no backend/Compose implementation in this workspace. Fixture tickets/statuses are demonstration data, not completed engineering work. This backlog is local Markdown, not imported into the running app.

Estimates are provisional effort: one day = eight focused working hours for one assigned worker, including scoped tests/review. FE: **15 days**; BE: **33 days**; combined **48 effort-days**, not elapsed time or an agent runtime promise. Dependency waits, available capacity and client capability uncertainty prevent a reliable completion date. Advanced timeline scheduling is excluded until its policy is confirmed in T-018/T-019; those estimates cover the stated baseline only.

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
| [T-010 — Verify Codex and Claude MCP client workflows](T-010-verify-codex-and-claude-client-workflows.md) | BE | BUILD | Open | Not applicable | 3 | Build |
| [T-011 — Stream committed project events with safe reconnect](T-011-stream-committed-project-events.md) | BE | BUILD | Open | Not applicable | 2 | Build |
| [T-012 — Package local Compose deployment and recovery](T-012-package-local-compose-and-recovery.md) | BE | BUILD | Open | Not applicable | 3 | Build |
| [T-013 — Connect frontend data access to authenticated REST](T-013-connect-frontend-to-authenticated-api.md) | FE | BUILD | Open | Not applicable | 2 | Build |
| [T-014 — Connect project and role screens to persistence](T-014-connect-project-and-role-screens.md) | FE | BUILD | Open | Not applicable | 1.5 | Build |
| [T-015 — Connect ticket board, document links and progress](T-015-connect-ticket-board-and-progress.md) | FE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-016 — Connect document editor and revision history](T-016-connect-document-editor-and-history.md) | FE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-017 — Connect live activity and approval request displays](T-017-connect-live-activity-and-approval-badges.md) | FE | BUILD | Open | Not applicable | 2 | Build |
| [T-018 — Persist ticket classification, estimates and planning data](T-018-persist-ticket-classification-and-estimates.md) | BE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-019 — Show ticket classifications, estimates and timeline context](T-019-show-ticket-estimates-and-planning-context.md) | FE | BUILD | Open | Not applicable | 2.5 | Build |
| [T-020 — Verify complete persisted desktop user journeys](T-020-verify-persisted-desktop-user-journeys.md) | FE | BUILD | Open | Not applicable | 2 | Build |

## Start here

Start T-001, then T-003. Shared service/API work unlocks frontend integration; preserve the existing screens. Client approval verification has explicit uncertainty and must fail closed. T-018 captures the new planning-field contract before MCP and planning UI use it. T-020 verifies the complete integrated journeys after feature-level checks.

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
| Shared foundation/delivery/end-to-end | T-001, T-012 | T-013, T-020 |

[Stories](../user-stories/README.md) · [Architecture](../technical-architecture/README.md) · [Approved screens](../designs/screens/README.md)
