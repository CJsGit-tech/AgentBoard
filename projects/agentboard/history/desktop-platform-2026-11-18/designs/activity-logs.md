# Activity logs

> Owner: Product Designer | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Review who worked on which ticket and when.

**Related stories:** US-010, US-011, US-013, US-014

**Required context:** [Interaction states](interaction-states.md) and [accessibility](accessibility.md).

- Use compact event rows: agent, ticket, action, time, outcome, labels and provenance. Distinguish agent-reported external events from operations observed by AgentBoard.
- Filter by project, ticket, observed client, type, labels, outcome, provenance and time. Clicking agent/event labels applies a relevant filter; it does not imply a complete live agent roster.
- Proposed initial range: 24 hours. Confirmed retention: rolling 30 days, with automatic expiry. Do not store or display full tool arguments/results by default.
- Preserve scroll while reviewing older events; buffer incoming events behind a New events button. Batch accessibility announcements.
- On disconnect, retain rows with a stale indicator and retry. Resume from retained event IDs; if expired, explain the gap and resynchronize.
- Empty logs do not prove no agent activity. Agent-reported dispatches and external tool calls are sufficient initially; the app does not launch or manage agents.

Product owner must review the proposed 24-hour default. Client reporting coverage remains an explicit limitation.
