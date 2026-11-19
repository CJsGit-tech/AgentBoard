# T-020 — Verify complete persisted desktop user journeys

Role: FE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-010, T-012, T-014, T-015, T-016, T-017, T-019
Estimate (days): 2
Estimate scope: Build
Estimate basis: Provisional: system-level regression and final evidence/review, not repeated feature development or unsupported browser/client certification.

## Outcome
Real desktop browser journeys pass through the packaged app and Postgres with saved reviewable evidence.

## Acceptance Criteria
- Run full create project/role/ticket/link/document/edit/history/restore flows, restart the app and verify persisted values in the browser.
- Exercise backend validation/unavailable responses, draft recovery, project isolation, status/progress consistency and live activity/approval display without fixture fallback.
- Record target host/browser, resized desktop and actual browser zoom/keyboard evidence; keep meaningful components separate and preserve approved visual constraints.
- Save build/type/browser results and independent review of final source; reference BE client compatibility/approval evidence rather than pretending browser tests prove agent approval.
- Report any genuine failures with actual observations as linked BUG tickets; do not invent reproductions or close this ticket while required checks remain unverified.

## Context
- [US-001](../user-stories/US-001-create-a-product-project.md)
- [US-002](../user-stories/US-002-find-and-switch-projects.md)
- [US-003](../user-stories/US-003-define-project-agent-roles.md)
- [US-004](../user-stories/US-004-create-and-prioritize-tasks.md)
- [US-005](../user-stories/US-005-assign-task-responsibility.md)
- [US-006](../user-stories/US-006-track-task-progress-and-blockers.md)
- [US-007](../user-stories/US-007-maintain-project-documents.md)
- [US-008](../user-stories/US-008-connect-documents-and-task-outputs.md)
- [US-009](../user-stories/US-009-review-project-progress.md)
- [US-010](../user-stories/US-010-review-a-task-s-changes.md)
- [US-011](../user-stories/US-011-operate-agentboard-through-mcp.md)
- [US-012](../user-stories/US-012-approve-agent-updates-and-deletions-in-the-client.md)
- [US-013](../user-stories/US-013-report-and-review-agent-activity.md)
- [US-014](../user-stories/US-014-expire-activity-after-30-days.md)
- [US-015](../user-stories/US-015-read-compare-and-restore-document-revisions.md)
- [security](../technical-architecture/security.md)
- [deployment-operations](../technical-architecture/deployment-operations.md)
- [Approved screen inventory](../designs/screens/README.md)
- [Assigned role](../../agents/frontend-programmer.md)

## Dependencies
- [T-010](T-010-verify-codex-and-claude-client-workflows.md)
- [T-012](T-012-package-local-compose-and-recovery.md)
- [T-014](T-014-connect-project-and-role-screens.md)
- [T-015](T-015-connect-ticket-board-and-progress.md)
- [T-016](T-016-connect-document-editor-and-history.md)
- [T-017](T-017-connect-live-activity-and-approval-badges.md)
- [T-019](T-019-show-ticket-estimates-and-planning-context.md)
