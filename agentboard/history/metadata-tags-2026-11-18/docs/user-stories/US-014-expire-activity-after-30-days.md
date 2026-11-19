> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

### US-014 — Expire activity after 30 days

- **Story:**
  - As a solo builder, I want activity to expire automatically so that the local log retains no more than 30 days by default.
- **Acceptance Criteria:**
  - Given an event at least 30 days old, when I query activity or task history, then it is excluded even if cleanup has not yet run.
  - Given expired activity, when automatic cleanup runs, then its event records are deleted without deleting current tickets, documents, or their retained revisions.
  - Given the application was stopped past a retention deadline, when it restarts, then expired events are hidden immediately and cleanup resumes.
  - Given the logging page loses its live connection, when reconnection succeeds, then it resumes from retained events and indicates any unavailable interval.
- **Associated Features:**
  - Progress tracking
