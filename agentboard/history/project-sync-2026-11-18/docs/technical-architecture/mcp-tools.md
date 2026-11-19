---
name: "MCP Tools"
description: "Expose AgentBoard operations to independent Codex/Claude clients."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:authorization", "concern:compatibility", "concern:security", "concern:auditability"]
---

# MCP Tools

> Owner: Solution Architect | Version: 0.1.4 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Expose AgentBoard operations to independent Codex/Claude clients.

## Tool Catalog

The [generated tool index](contracts/mcp/README.md) is the canonical navigation for names, permissions, schemas and examples. This table summarizes responsibilities only.

Typed JSON input/output. Reuse [REST contracts](api-contracts.md), project checks, services, errors, concurrency and idempotency rules.

| Family | Responsibility |
| --- | --- |
| Projects | Project records |
| Roles | Agent responsibility definitions |
| Tickets | Ownership, priority and progress |
| Documents | Content and ticket associations |
| History | Retained versions, comparison and restore |
| Activity | Report/filter events and read progress |
| Requests | Pending request state and client approval retry |

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

## Schemas and Examples

[Choose a tool](contracts/mcp/README.md) to open its input/output schema and examples. The [catalog JSON](contracts/mcp/tools.json) references the same shared field definitions used by REST.

For `update_ticket`: [schema](contracts/mcp/update-ticket.schema.json), [input](examples/mcp/update-ticket.input.json), [pending approval](examples/mcp/update-ticket.output.json), [applied](examples/mcp/update-ticket.applied.json), [rejected](examples/mcp/update-ticket.rejected.json), [stale revision](examples/mcp/update-ticket.conflict.json).

These outputs are application structured payloads, not MCP/JSON-RPC envelopes. Resolve local schema references before publishing through an SDK. A schema-valid response does not prove client approval, mutation atomicity or compatibility; existing release gates still apply.
