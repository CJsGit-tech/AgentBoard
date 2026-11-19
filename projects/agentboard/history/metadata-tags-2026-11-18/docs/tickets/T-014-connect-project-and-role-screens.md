# T-014 — Connect project and role screens to persistence

Role: FE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-002, T-013
Estimate (days): 1.5
Estimate scope: Build
Estimate basis: Provisional: existing forms/screens reused; feature wiring, targeted browser tests and review only.

## Outcome
Approved project and role screens operate on persisted data without losing context or input.

## Acceptance Criteria
- Wire existing create/edit/list/switch flows to the production adapter; preserve stable IDs and show server-saved results after reload.
- Prevent stale project responses from replacing the selected project; distinguish same-name projects using available identity details.
- Retain invalid/failed inputs and existing role assignments; show actionable delete/conflict errors without claiming success.
- Save targeted browser evidence for create/reload/edit/switch/failure paths while retaining approved desktop/keyboard presentation.

## Context
- [US-001](../user-stories/US-001-create-a-product-project.md)
- [US-002](../user-stories/US-002-find-and-switch-projects.md)
- [US-003](../user-stories/US-003-define-project-agent-roles.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [Approved screen inventory](../designs/screens/README.md)
- [Existing implementation](../../frontend/src/features/projects/ProjectsScreen.tsx)
- [Assigned role](../../agents/frontend-programmer.md)

## Dependencies
- [T-002](T-002-persist-projects-and-agent-roles.md)
- [T-013](T-013-connect-frontend-to-authenticated-api.md)
