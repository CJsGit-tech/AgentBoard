> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

### US-006 — Track task progress and blockers

- **Story:**
  - As a solo builder, I want to update task status and record blockers so that I can coordinate work and identify what needs intervention.
- **Acceptance Criteria:**
  - **Given** a task, **when** I select Planned, In Progress, Blocked, or Done and save, **then** the task displays that status and its last update time.
  - **Given** a task being marked Blocked, **when** I save without a blocker explanation, **then** the app requests an explanation before applying the change.
  - **Given** a blocked task, **when** I resolve the blocker and change its status, **then** it no longer appears as currently blocked.
  - **Given** a completed task requiring more work, **when** I return it to In Progress, **then** it reappears among active work.
  - **Given** a failed status save, **when** the update fails, **then** the app retains the last saved status and clearly shows the failure with a retry option.
- **Associated Features:**
  - Task coordination
  - Progress tracking
