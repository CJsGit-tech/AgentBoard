> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

### US-012 — Approve agent updates and deletions in the client

- **Story:**
  - As a solo builder, I want to review agent Update/Delete requests in Codex or Claude so that agents cannot change existing work without my approval.
- **Acceptance Criteria:**
  - Given an agent Update/Delete request, when it arrives, then the existing record remains unchanged until I approve the specific target and proposed change through the client interface.
  - Given a pending request associated with a ticket, when I view the board, then its ticket shows a Needs approval badge separately from Planned, In Progress, Blocked, or Done status.
  - Given approval for a change, when it commits, then the approved change and its audit record are saved together and the badge clears only if no other pending requests remain.
  - Given rejection, timeout, cancellation, or unsupported client approval, when processing finishes, then no business change executes; unsupported approval leaves a pending request and Needs approval badge for later retry.
  - Given a record changed after approval was requested, when an old approval is submitted, then the change is rejected as stale and fresh approval is required.
  - Given an agent assertion that approval was granted, when no verified client approval response exists, then the assertion does not authorize the change.
- **Associated Features:**
  - Task coordination
  - Progress tracking
  - Document management
  - Agent role management
  - Product project management
