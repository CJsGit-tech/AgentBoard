# Shared interaction states

> Owner: Product Designer | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Define common behavior once for every work surface.

**Related stories:** Cross-cutting

**Required context:** None.

| State | Required behavior |
| --- | --- |
| Hover / focus / selection | Subtle surface hover; visible 2px inset keyboard-focus indicator; no outside halo; distinguish selection |
| Initial loading | Skeletons matching structure |
| Refresh | Retain previous values with refresh indicator |
| Empty | Explain absence and offer relevant creation action; absence is not proof of no activity |
| Error | Explain and offer retry; never replace unavailable metrics with zero |
| Saving / success | Prevent duplicate submission; honor idempotency; acknowledge canonical server result once |
| Unsaved | Retain input; warn before navigation or closing; Escape must not silently discard |
| Conflict | Show newer server content alongside draft; no blind overwrite |
| Missing / expired | Explain unavailable record, revision or approval; provide recovery route |
| Disconnected | Keep prior data, label stale state, offer retry |

Use 120–180ms color/opacity transitions; reduced motion disables transitions. Do not animate counters. These are specifications, not implemented components.

Control focus must remain inside widget borders. Dropdown arrows reserve internal padding and never overlap or extend beyond control borders.
