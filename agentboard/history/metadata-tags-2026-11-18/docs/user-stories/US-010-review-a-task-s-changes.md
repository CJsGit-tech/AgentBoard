> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

### US-010 — Review a task's changes

- **Story:**
  - As a solo builder, I want to inspect task ownership and status changes so that I can reconstruct how work progressed.
- **Acceptance Criteria:**
  - **Given** a saved ownership or status change, **when** I inspect task activity, **then** I see the previous value, new value, and time of the change.
  - **Given** several changes, **when** I inspect activity, **then** their order is clear and reopening the task preserves the recorded entries.
  - **Given** an update that failed to save, **when** I inspect activity, **then** no successful change is recorded for that failed attempt.
  - **Given** a task with no retained changes, **when** I inspect activity, **then** an empty state explains that no activity is available within the 30-day retention window.
- **Associated Features:**
  - Progress tracking
  - Task coordination
