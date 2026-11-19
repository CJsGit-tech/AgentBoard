---
name: "AgentBoard · screen coverage"
description: "Lists approved desktop mockup coverage, scope, evidence, and run instructions."
kind: "screen-inventory"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:accessibility", "concern:authorization", "concern:reliability", "concern:data-integrity"]
---

# AgentBoard · screen coverage

**Status: approved — user approved the reviewed mocked desktop frontend on 2026-11-18.**

Canonical source: `frontend/` (React + Vite + TypeScript). The screen approval below covered the earlier mocked UI baseline only. Since that review, the app gained a connected frontend, FastAPI backend, PostgreSQL persistence, MCP endpoints, client-approval flows, migrations, and a Docker Compose deployment. The historical mockup approval does not certify those later integrations or an internet-facing deployment; see the [review report](../../review-report.md) and [operations guide](../../technical-architecture/deployment-operations.md).

Confirmed environment: personal computer, desktop browser, keyboard/pointer; local Docker Compose remains the production target. Phone layouts are outside scope. Review window widths: 1600, 1280 and 900px; actual Chrome 200% zoom evidence is saved separately.

## Run

From `frontend/`: `npm install`, then `npm run dev -- --port 4203 --strictPort`. Current run uses checksum-verified temporary Node at `/private/tmp/node-v24.22.3-darwin-arm64/bin`; prepend it to PATH if the terminal lacks Node/npm. No system Node install was changed. Open http://127.0.0.1:4203/.

Use `npm run typecheck`, `npm run build`, `npm run test:ui` for reproducible checks. UI tests use installed Google Chrome. This preview server is loopback-only, not a production Compose deployment.

## Complete screen inventory

Each row passed independent final verification for the mocked frontend scope. Dialogs/inspectors are included as screen states, not forced into separate routes.

The earlier approval covers only the rows implemented below. The connected frontend implements the tag filters and Markdown upload review required by US-016 and US-017. The earlier visual approval did not include these states. See the [runtime verification report](../../review-report.md) for connected behavior.

| Screen/state | Canonical source | Stories | Required behavior/state coverage |
| --- | --- | --- | --- |
| Projects | [source](../../../frontend/src/features/projects/ProjectsScreen.tsx) | US-001, US-002 | List/search/identity, empty/error/loading, project isolation |
| Project create/edit | [source](../../../frontend/src/features/projects/ProjectForm.tsx) | US-001, US-002 | Validation, retained failed-save input, preserved associations, unsaved close |
| Overview | [source](../../../frontend/src/features/overview/OverviewScreen.tsx) | US-009, US-012 | Saved counts, status navigation, blockers, approval badge, no-task/error |
| Roles | [source](../../../frontend/src/features/roles/RolesScreen.tsx) | US-003, US-005 | Project-scoped roles, responsibilities, assignment preserved |
| Role create/edit | [source](../../../frontend/src/features/roles/RoleForm.tsx) | US-003 | Required fields, error retention, native dialog keyboard behavior |
| Tickets table/board | [source](../../../frontend/src/features/tickets/TicketsScreen.tsx) | US-004, US-005, US-006 | Filters/order, four statuses, separate approval badge, shared records |
| Ticket create/detail/edit | [source](../../../frontend/src/features/tickets/TicketInspector.tsx) | US-004, US-005, US-006, US-008, US-010, US-012 | Ownership/status/blocker, failure/conflict draft, linked context/output, activity, protected request states |
| Documents | [source](../../../frontend/src/features/documents/DocumentsScreen.tsx) | US-007 | Project list, search, create/empty/error |
| Document reader | [source](../../../frontend/src/features/documents/DocumentDetailScreen.tsx) | US-007, US-008 | Content/outline/current metadata, linked-ticket return, missing document |
| Document create/edit | [source](../../../frontend/src/features/documents/DocumentEditor.tsx) | US-007 | Title/content required, revisions on save, failure/conflict draft, browser Back guard |
| Revision history | [source](../../../frontend/src/features/documents/DocumentHistoryScreen.tsx) | US-015 | Two retained revisions compared, current + three previous, restore/expiry/return |
| Activity | [source](../../../frontend/src/features/activity/ActivityScreen.tsx) | US-010, US-011, US-013, US-014 | Ticket/agent/type/label/outcome/provenance/time, observed/reported, live buffer/reconnect/gap/dedupe/retention |

## Feature → component → source

Meaningful visual components are implemented in separate files; route wiring, fixtures, nonvisual helpers and state logic are separate. The following is a navigation map, not proof of semantic compliance.

| Feature/responsibility | Component file |
| --- | --- |
| Shared UI · ApprovalBadge | [source](../../../frontend/src/components/ApprovalBadge.tsx) |
| Shared UI · Modal | [source](../../../frontend/src/components/Modal.tsx) |
| Shared UI · OperationNotice | [source](../../../frontend/src/components/OperationNotice.tsx) |
| Shared UI · PageHeader | [source](../../../frontend/src/components/PageHeader.tsx) |
| Shared UI · PreviewToolbar | [source](../../../frontend/src/components/PreviewToolbar.tsx) |
| Shared UI · SaveFailureControl | [source](../../../frontend/src/components/SaveFailureControl.tsx) |
| Shared UI · Sidebar | [source](../../../frontend/src/components/Sidebar.tsx) |
| Shared UI · StatePanel | [source](../../../frontend/src/components/StatePanel.tsx) |
| Shared UI · StatusBadge | [source](../../../frontend/src/components/StatusBadge.tsx) |
| Shared UI · WorkspaceShell | [source](../../../frontend/src/components/WorkspaceShell.tsx) |
| Activity · ActivityFeed | [source](../../../frontend/src/features/activity/ActivityFeed.tsx) |
| Activity · ActivityFilters | [source](../../../frontend/src/features/activity/ActivityFilters.tsx) |
| Activity · ActivityScreen | [source](../../../frontend/src/features/activity/ActivityScreen.tsx) |
| Activity · LiveActivityControls | [source](../../../frontend/src/features/activity/LiveActivityControls.tsx) |
| Documents · DocumentContent | [source](../../../frontend/src/features/documents/DocumentContent.tsx) |
| Documents · DocumentDetailScreen | [source](../../../frontend/src/features/documents/DocumentDetailScreen.tsx) |
| Documents · DocumentEditor | [source](../../../frontend/src/features/documents/DocumentEditor.tsx) |
| Documents · DocumentHistoryScreen | [source](../../../frontend/src/features/documents/DocumentHistoryScreen.tsx) |
| Documents · DocumentList | [source](../../../frontend/src/features/documents/DocumentList.tsx) |
| Documents · DocumentOutline | [source](../../../frontend/src/features/documents/DocumentOutline.tsx) |
| Documents · DocumentsScreen | [source](../../../frontend/src/features/documents/DocumentsScreen.tsx) |
| Documents · RevisionComparison | [source](../../../frontend/src/features/documents/RevisionComparison.tsx) |
| Documents · RevisionList | [source](../../../frontend/src/features/documents/RevisionList.tsx) |
| Documents · RevisionRestore | [source](../../../frontend/src/features/documents/RevisionRestore.tsx) |
| Documents · UnavailableRevision | [source](../../../frontend/src/features/documents/UnavailableRevision.tsx) |
| Overview · BlockerList | [source](../../../frontend/src/features/overview/BlockerList.tsx) |
| Overview · OverviewScreen | [source](../../../frontend/src/features/overview/OverviewScreen.tsx) |
| Overview · ProgressSummary | [source](../../../frontend/src/features/overview/ProgressSummary.tsx) |
| Projects · ProjectCard | [source](../../../frontend/src/features/projects/ProjectCard.tsx) |
| Projects · ProjectForm | [source](../../../frontend/src/features/projects/ProjectForm.tsx) |
| Projects · ProjectsScreen | [source](../../../frontend/src/features/projects/ProjectsScreen.tsx) |
| Roles · RoleCard | [source](../../../frontend/src/features/roles/RoleCard.tsx) |
| Roles · RoleForm | [source](../../../frontend/src/features/roles/RoleForm.tsx) |
| Roles · RolesScreen | [source](../../../frontend/src/features/roles/RolesScreen.tsx) |
| Tickets · ApprovalRequestPanel | [source](../../../frontend/src/features/tickets/ApprovalRequestPanel.tsx) |
| Tickets · TicketActivity | [source](../../../frontend/src/features/tickets/TicketActivity.tsx) |
| Tickets · TicketBoard | [source](../../../frontend/src/features/tickets/TicketBoard.tsx) |
| Tickets · TicketCard | [source](../../../frontend/src/features/tickets/TicketCard.tsx) |
| Tickets · TicketDocumentLinks | [source](../../../frontend/src/features/tickets/TicketDocumentLinks.tsx) |
| Tickets · TicketEditor | [source](../../../frontend/src/features/tickets/TicketEditor.tsx) |
| Tickets · TicketFilters | [source](../../../frontend/src/features/tickets/TicketFilters.tsx) |
| Tickets · TicketInspector | [source](../../../frontend/src/features/tickets/TicketInspector.tsx) |
| Tickets · TicketTable | [source](../../../frontend/src/features/tickets/TicketTable.tsx) |
| Tickets · TicketsScreen | [source](../../../frontend/src/features/tickets/TicketsScreen.tsx) |

## Evidence and limitations

[Independent reviewer report](evidence/run-003-create-screens/reviewer-report.md) and [guidance review](evidence/run-003-create-screens/guidance-review.md) record current-source verification. [Evidence manifest](evidence/latest.json) maps checks and captures to the reviewed source. Technical verification: passed; human screen approval recorded on 2026-11-18.

Existing screens were reused. Revalidation corrected clickable Activity agent/label filters and contextual descriptions for repeated Edit buttons. Build, type checking, 14 app browser tests, 5 independent edge tests, changed-control keyboard/layout checks, nine-route axe audit and 17 representative contrast pairs passed. Fresh changed-screen captures accompany retained unaffected captures, with applicability assessed by the reviewer. Earlier evidence and failed attempts remain preserved.

Mandatory legacy scan: zero findings across 52 rules/38 guides on authored frontend/src. Its limited coverage does not certify overall UI quality. Guidance used: dialog, responsive-table, forms, accessibility; full retrieved text remains in run-001.

[Captures](captures/) include existing screens/states and native Chrome 200% zoom evidence. Updated Activity, Projects and Roles images are in [current review evidence](evidence/run-003-create-screens/reviewer-tests/). The screenshots and approval record describe the earlier visual review. Current application behavior is connected to the backend; its runtime limits and operational checks are documented separately. Chrome testing is not cross-browser or full assistive-technology certification; automated contrast audit was incomplete and representative contrast was assessed separately. Screen approval is recorded in [approval record](approval.md), and authoritative design navigation now links this implementation.
