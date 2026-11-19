# MCP Tools

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Expose AgentBoard operations to independent Codex/Claude clients.

## Tool Catalog

Typed JSON input/output. Reuse [REST contracts](api-contracts.md), project checks, services, errors, concurrency and idempotency rules.

| Family | Tools |
| --- | --- |
| Projects | `list_projects`, `get_project`, `create_project`, `update_project`, `delete_project` |
| Roles | `list_roles`, `get_role`, `create_role`, `update_role`, `delete_role` |
| Tickets | `list_tickets`, `get_ticket`, `create_ticket`, `update_ticket`, `delete_ticket` |
| Documents | `list_documents`, `get_document`, `create_document`, `update_document`, `delete_document`, `link_document`, `unlink_document` |
| History | `list_document_versions`, `get_document_version`, `compare_document_versions`, `restore_document_version` |
| Activity | `append_activity`, `list_activity`, `get_project_progress` |
| Requests | `get_mutation_request`, `retry_mutation_request` for unchanged pending payloads |

Status/owner changes are updates. [Approval flow](approval-flow.md) owns all mutation authorization.

## Transport — Proposed

| Boundary | Design |
| --- | --- |
| Default | Authenticated loopback Streamable HTTP at `/mcp` |
| Stdio-only configuration | Optional thin bridge relaying capabilities, cancellation and approval; no separate database or authorization bypass |
| Identity | Locally registered integration with scoped credential; no hosted identity provider |
| Request security | Validate Origin/Host; reject unauthenticated calls; keep MCP credentials separate from browser cookies/CSRF |

Never interpret untrusted text as approval. Native client and bridge behavior need separate tests.

## Client Compatibility Gate

For **each** Codex desktop, Codex CLI, Claude Code and Claude Desktop configuration, test:

- Protocol/version negotiation; tool discovery and calls; Create/Read.
- Approval accept, decline and unsupported behavior; stale changes.
- Restart/reconnect, duplicate calls, revision reads and activity append.

Choose SDK/protocol versions from actual client support. Until tested, compatibility is **unverified**; unsupported approval must fail closed.
