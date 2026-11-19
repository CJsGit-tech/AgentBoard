# MCP Tools

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## MCP Tools


Typed JSON input/output; same project checks, services, error codes, concurrency and idempotency rules as REST. Initial explicit tool families:

| Family | Tools / behavior |
| --- | --- |
| Projects | list_projects, get_project, create_project, update_project, delete_project |
| Roles | list_roles, get_role, create_role, update_role, delete_role |
| Tickets | list_tickets, get_ticket, create_ticket, update_ticket, delete_ticket; status/owner edits are updates |
| Documents | list_documents, get_document, create_document, update_document, delete_document; link_document, unlink_document |
| History | list_document_versions, get_document_version, compare_document_versions, restore_document_version |
| Activity | append_activity, list_activity, get_project_progress |
| Approvals | get_mutation_request, retry_mutation_request (re-runs client approval for unchanged pending payload) |


Authorization rules: [approval flow](approval-flow.md).

## Transport and client verification

Prefer authenticated loopback Streamable HTTP at `/mcp`. For stdio-only client configurations, provide a local bridge that relays protocol features without interpreting untrusted text as approval. Register each integration locally with a scoped credential; no hosted identity provider. Keep browser cookie/CSRF and MCP credentials separate. Validate HTTP Origin/Host; reject unauthenticated connections.

Compatibility release gate per Codex desktop, Codex CLI, Claude Code, and Claude Desktop: initialization/version negotiation; list/call tools; CR; approval accept/decline/unsupported; restart/reconnect; duplicate call; stale mutation; revision reads; activity append. Until these tests run, do not claim universal working support. Older and newer protocol versions differ; choose SDK and protocol versions from actual client support. All adapters must fail closed for unsupported approval.
