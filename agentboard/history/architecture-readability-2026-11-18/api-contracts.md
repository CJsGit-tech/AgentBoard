# Browser REST contracts

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## 6. API / Interface Contracts — Browser REST

Prefix `/api/v1`. Project-scoped resource collections: `/projects`, `/projects/{p}/roles`, `/projects/{p}/tickets`, `/projects/{p}/documents`. Collection GET/POST and individual GET/PATCH/DELETE implement explicit supported operations; project/role/ticket deletion behavior is constrained below. Additional routes:

- `/projects/{p}/tickets/{t}/documents`: list/create associations; targeted DELETE removes the link only.
- `/projects/{p}/documents/{d}/versions`: list/read retained versions; `/compare` accepts two retained IDs; `/restore` creates a new current version.
- `/projects/{p}/progress`: counts by status plus separate pending-approval counts.
- `/projects/{p}/activity`: filters by ticket, agent, event_type, labels, time, outcome, provenance.
- `/mutation-requests/{id}`: read request/result; browser provides visibility, not an agent-approval inbox or approve endpoint.
- `/events`: same-origin SSE with project filters, retained event IDs and reconnect cursor. Client refetches canonical records after notifications; no document bodies in events.

Delete semantics: document deletion removes its versions and associations; ticket deletion removes its associations/pending requests and retains only bounded audit metadata; role deletion is rejected while assigned; project deletion is rejected while it contains records in this release. Every agent deletion goes through client approval. Explicitly describe consequences in the approval summary. Never silently cascade deletion of a populated project.

Create returns 201, reads/updates 200, successful deletion 204. Invalid fields 422, missing/cross-project resource 404, stale revision 409, authorization failure 401/403, temporary database failure 503. Errors: `{error: {code, message, fields}, request_id}`. Revision-required mutations reject stale writes rather than overwrite. Bounded pagination default 50/max 100, deterministic tie-break by ID. Creates accept client operation keys; same key+payload returns the prior result, different payload returns conflict. Reference limits proposed: 1 MiB document; 2 KiB activity summary; bounded labels. Rejected input preserves the UI draft.
