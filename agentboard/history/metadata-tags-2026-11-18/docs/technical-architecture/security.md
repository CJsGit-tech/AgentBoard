# Security and Nonfunctional Requirements

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Define access boundaries, privacy safeguards and observable quality requirements.

## Security & Nonfunctional Requirements

| Boundary | Rule |
| --- | --- |
| Local access | Trust the OS account; loopback exposure still requires application authorization |
| Pairing | First-run browser session and per-client credentials; no shared model/provider keys |
| Browser requests | Host/Origin, content type, size and CSRF checks |
| Agent access | Separate credentials; cannot impersonate browser user actions or bypass [approval](approval-flow.md) |
| Containers | Non-root where supported; no Docker socket or arbitrary host filesystem mounts |
| Document rendering | Markdown raw HTML disabled; safe links |
| Secrets | Restrict credential files; exclude bodies/tokens from logs |

## Logging Privacy

[Activity logging](activity-logging.md) owns event content, provenance and retention. Also:

- Rotate operator/container logs and expire them within 30 days.
- Do not create another durable full-payload log.
- Remove sensitive payloads from pending-request audit metadata after resolution.

## Live Delivery — Proposed

```text
Committed Postgres event → retained-ID polling → SSE → UI refetch
```

| Decision | Reason / failure behavior |
| --- | --- |
| One backend worker initially | Simple local baseline; benchmark before scaling |
| Persisted IDs across backend/maintenance | Correct replay remains authoritative |
| Later LISTEN/NOTIFY | May reduce latency; never replaces persisted replay |
| Expired reconnect cursor | Resync canonical records |
| Under two-second local updates | Proposed target; not measured |

## Verification Checklist

- Project isolation; atomic mutations/audit; idempotent Create and event append.
- Unsupported approval, separate badge, multiple requests, stale/replayed decisions and rejected deletes.
- Concurrent history pruning, restore-as-new-version, retention after downtime.
- SSE recovery and failed-save draft recovery.
- Keyboard operation and non-color-only status/badges.

Covers US-001–015. Select a benchmark machine and budgets using the [proposed workload](constraints.md). These are test requirements, not executed results.
