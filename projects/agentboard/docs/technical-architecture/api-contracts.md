---
name: "Browser REST Contracts"
description: "Specifies browser API operations and errors, with project events streamed at `/events`."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:data-integrity", "concern:security", "concern:reliability", "concern:compatibility"]
---

# Browser REST Contracts

> Owner: Solution Architect | Version: 0.1.6 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Specify browser operations and observable error behavior. Domain routes use `/api/v1`; the live stream is root `/events`, matching the proxy design.

AgentBuild-connected commands use the same project-scoped REST/MCP contracts as the UI and write directly to canonical app records. Local fallback files do not synchronize automatically.

`GET /projects/{p}/tickets` and `/documents` accept repeatable `feature_tags` and `concern_tags` filters. A record matches any selected tag within each namespace and must match each nonempty namespace. MCP `list_tickets` and `list_documents` use the same filters. Returned records include their tags. `GET /projects/{p}/tags` lists the registered tag IDs for selectors. A project registers its tag vocabulary as a `metadata-catalog` document before assigning those tags to another document or ticket.

Documents store `title`, short `description`, `kind`, `tags`, and `content` separately. Tickets store the skill's FE/BE execution role, BUG/BUILD type, verification, assignment, estimates and tags beside the app workflow status. `Needs approval` stays separate from status. See the [data model](data-model.md) and [AgentBuild integration](agentbuild-integration.md).

External Markdown uploads use a separate user-reviewed preview flow. The preview extracts and validates metadata against the project vocabulary, marks source-provided values, and commits only after the user confirms. A reviewed upload uses the regular document Create request with `source: upload` and the original filename in `source_id`. The server assigns `created_at` as the upload time. The initial document body and exact `original_frontmatter` prefix preserve the submitted text. The preview checks the UTF-8 size of the complete request before submission. AgentBuild uses direct MCP writes for its own artifacts.

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
