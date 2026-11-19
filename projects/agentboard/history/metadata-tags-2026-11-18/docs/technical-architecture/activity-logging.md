# Activity Logging and Retention

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Define a minimal, filterable activity trail and its lifetime.

## Event Content

| Field | Meaning |
| --- | --- |
| Agent/client; project; ticket when relevant | Who worked on what; no invented ticket association |
| Action/event type; outcome; labels | What happened and how it can be filtered |
| `received_at` | Server receipt time; authoritative retention clock |
| `occurred_at` | Reported action time; displayed as reported |
| Provenance | Server-observed API/MCP/maintenance or agent-reported external activity |

- AgentBoard audits its own operations; agents report external dispatches/tool calls/work.
- Full external capture is not promised. Reported activity is not independent verification.
- Exclude full prompts, tool arguments/results, document bodies and secrets by default.
- Deduplicate retried event keys. A log append must not recursively log itself forever.

## Retention

| Data | Lifetime / cleanup |
| --- | --- |
| Activity and task history | Visible only while `received_at > server_now - 30 days` |
| Expired activity | Delete in bounded batches; at least hourly and at startup is **proposed** |
| Terminal approval audit details | Prune after 30 days |
| Pending approval payload | **Proposed:** expire and purge after 24 hours; show an expired outcome |
| Backup copies | Separate bounded retention; filter/clean restored data before serving |

Query and SSE replay filters enforce the cutoff even before physical cleanup, including after the machine was stopped. Cadence and pending-request lifetime are implementation proposals, not confirmed product timings.

**Related:** [Live delivery](security.md) · [Approval flow](approval-flow.md) · [Backup/restore](deployment-operations.md)
