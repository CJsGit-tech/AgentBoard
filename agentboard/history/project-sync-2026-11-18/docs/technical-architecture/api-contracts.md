---
name: "Browser REST Contracts"
description: "Specifies browser API operations and errors, with project events streamed at `/events`."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:data-integrity", "concern:security", "concern:reliability", "concern:compatibility"]
---

# Browser REST Contracts

> Owner: Solution Architect | Version: 0.1.4 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Specify browser operations and observable error behavior. Domain routes use `/api/v1`; the live stream is root `/events`, matching the proxy design.

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

## Machine-Readable Contract

[OpenAPI 3.1.1 JSON](contracts/openapi.json) defines operations, UUID parameters, bodies, response codes, local-session/CSRF requirements and shared schema references. This is a draft design, not a deployed API.

[Create ticket request](examples/api/create-ticket.request.json) · [201 response](examples/api/create-ticket.response.json) · [Update request](examples/api/update-ticket.request.json) · [409 conflict](examples/api/update-ticket.conflict.json) · [Progress response](examples/api/project-progress.response.json)

Examples contain JSON bodies only; headers and path/query parameters come from OpenAPI. A 204 response has no JSON body, and SSE is a stream. Exact wire names, field bounds and pagination shape are implementation proposals; [contract conventions](contracts/README.md) explain their scope.
