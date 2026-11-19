# Browser REST Contracts

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Specify browser operations and observable error behavior. All routes below use `/api/v1`.

## API / Interface Contracts

| Resource | Operations |
| --- | --- |
| `/projects` | Collection GET/POST; individual GET/PATCH/DELETE where supported |
| `/projects/{p}/roles`, `/tickets`, `/documents` | Project-scoped collections and individual records |
| `/projects/{p}/tickets/{t}/documents` | List/create associations; targeted DELETE unlinks only |
| `/projects/{p}/documents/{d}/versions` | List/read history; `/compare` accepts two retained IDs; `/restore` creates a new current version |
| `/projects/{p}/progress` | Counts by task status; pending-approval counts separate |
| `/projects/{p}/activity` | Filter ticket, agent, type, labels, time, outcome and provenance |
| `/mutation-requests/{id}` | Read request/result; no browser agent-approval inbox or approve endpoint |
| `/events` | Same-origin SSE, project filters, retained IDs and reconnect cursor; no document bodies |

Paths such as `/tickets` above are relative to the shown project prefix. Notifications cause clients to refetch canonical records.

## Responses

| Condition | HTTP result |
| --- | --- |
| Create / read or update / delete | 201 / 200 / 204 |
| Invalid fields / missing or cross-project record | 422 / 404 |
| Stale revision | 409; never overwrite |
| Authentication / authorization failure | 401 / 403 |
| Temporary database failure | 503 |

Error shape: `{error: {code, message, fields}, request_id}`. Failed input/save retains the UI draft.

- Pagination: default 50, maximum 100; deterministic ID tie-break.
- Create operation key + same payload returns the prior result; different payload returns conflict.
- **Proposed limits:** 1 MiB/document, 2 KiB/activity summary, bounded labels.

## Delete Consequences

| Target | Behavior |
| --- | --- |
| Document | Remove versions and associations |
| Ticket | Remove associations/pending requests; retain bounded audit metadata |
| Assigned role | Reject deletion |
| Nonempty project | Reject; never silently cascade |

Every agent deletion requires [client approval](approval-flow.md), showing these consequences.
