> Owner: Product Manager | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-17

### US-013 — Report and review agent activity

- **Story:**
  - As a solo builder, I want a logging page showing agent work on tickets so that I can review dispatches, tool calls, and changes in one place.
- **Acceptance Criteria:**
  - Given an agent dispatch, tool call, or external work event, when the agent reports it through MCP, then the log shows agent, ticket when applicable, action, timestamp, outcome, and filterable labels.
  - Given an operation handled by AgentBoard itself, when it completes or fails, then AgentBoard records it automatically and distinguishes server-observed events from agent-reported events.
  - Given activity logs, when I filter by project, ticket, agent, event type, label, or time, then the view shows matching retained events only.
  - Given new committed activity, when I keep the logging page open, then entries appear automatically without manual refresh.
  - Given duplicate event delivery with the same event key, when the event is retried, then only one log entry is retained.
  - Given an unreported external action, when I review the log, then the app does not claim that its external capture is exhaustive.
- **Associated Features:**
  - Progress tracking
  - Task coordination
  - Agent role management
