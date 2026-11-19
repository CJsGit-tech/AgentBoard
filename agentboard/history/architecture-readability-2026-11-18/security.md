# Security and nonfunctional requirements

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## 9. Security & Nonfunctional Requirements

Local OS account is trusted; loopback-only exposure is required, not an authentication substitute. First-run local pairing creates browser session and per-client credentials. No shared model/provider keys. Restrict credential files; validate HTTP Host/Origin, content types, request sizes, and CSRF on browser mutations. MCP tools cannot impersonate browser user actions. Do not expose a generic agent-accessible route that bypasses approval. Run containers non-root where supported, without host Docker socket or arbitrary host filesystem access. Render document Markdown with raw HTML disabled and safe links.

Event provenance is visible: API-observed, MCP-observed, agent-reported, maintenance. Agent-reported identity/times are not presented as independent verification. Logs default to minimal metadata. Operator/container logs must also be rotated and expire within 30 days; redact bodies/tokens, and avoid adding a second durable full-payload log. Exclude sensitive payloads from pending-request audit metadata after resolution.

Live delivery uses SSE plus Postgres as the source of truth; proposed one backend worker initially. Poll retained event IDs for correctness across backend/maintenance processes; future LISTEN/NOTIFY can reduce latency without replacing persisted replay. Reconnect resyncs canonical records when a cursor has expired. Proposed live target under two seconds locally; benchmark rather than claim achieved performance.

Tests cover US-001–015: project isolation, atomic mutations/events, unsupported approval and visible badge, multiple pending requests, stale or replayed approval, rejected deletes, idempotent CR/log append, document history pruning under concurrent writes, restoring creates a new version, retention after downtime, SSE recovery, and failed save recovery. Proposed reference workload is the envelope in section 2; select the benchmark machine and budgets during implementation. Keyboard and non-color-only status/badges are required.
