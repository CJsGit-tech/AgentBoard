# Activity Logging and Retention

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

Activity logs cover server-observed operations plus agent-reported dispatch/tool/work events; full external capture is explicitly not promised. Minimal payload: agent, ticket if relevant, action, outcome, timestamps, labels, provenance. No full prompts, tool arguments, results, document bodies, or secrets by default. Recording a log event must not recursively log its own log write forever.

Use server received_at as the retention clock; preserve reported occurred_at for display and label it as reported. All activity queries/SSE replay enforce received_at > server_now - 30 days, regardless of cleanup lag. Maintenance deletes expired rows in bounded batches at least hourly and immediately at startup. Task history uses the same events and retention. Prune terminal approval audit details after 30 days; pending approval payloads expire after a proposed 24 hours and are purged, with a visible expired outcome. Exact operational retention cadence is a proposal; content remains inaccessible after expiry even if the machine was stopped. Backups are separate point-in-time copies and must have their own bounded retention; restored data is filtered/cleaned before serving.
