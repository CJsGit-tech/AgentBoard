---
name: "AgentBoard Contracts"
description: "Find precise schemas without loading every example or implementation detail."
kind: "contract-index"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:security", "concern:authorization", "concern:compatibility", "concern:data-integrity"]
---

# AgentBoard Contracts

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Find precise schemas without loading every example or implementation detail.

| Need | Read |
| --- | --- |
| Browser HTTP operations | [OpenAPI 3.1.1 JSON](openapi.json) |
| One MCP tool | [Tool index](mcp/README.md) → its input/output schema |
| Record / shared wire fields | [Domain JSON Schema](schemas/domain.schema.json) · [representation notes](schemas/README.md) |
| Example payloads | [Examples index](../examples/README.md) |
| Validation bindings | [Manifest](manifest.json) |

## Authority and Scope

- Schemas define fields, types, required values and allowed outcomes. Examples illustrate them; they are not separate specifications.
- Markdown owns business rationale, transaction rules, trust boundaries and operational policy. JSON does not establish database foreign keys or runtime authorization.
- Contracts are draft implementation proposals derived from the confirmed requirements. Exact field spellings, wire enum values, pagination shape, operation keys and limits need implementation review; no API/server is running.
- Entity records use UUIDs and UTC `Z` timestamps. Ticket UI labels map to wire values `planned`, `in_progress`, `blocked`, `done`; priorities use `high`, `normal`, `low`.
- `needs_approval` exists only in the **TicketView read projection**. Persisted TicketRecord and task status never store it as status.
- Browser REST assumes a local user session plus CSRF on mutations. MCP uses its separately authenticated connection and the existing client-approval policy. There is no approve endpoint/tool or `approved=true` argument.
- Contract-level name/label bounds and examples are proposed constraints. The 1 MiB document and 2 KiB summary limits are byte limits enforced by services; JSON Schema string lengths alone do not prove byte-size compliance.
- Link/unlink revision checks refer to the parent ticket revision; association changes must invalidate stale ticket approvals. Document restore uses the document revision. This is an explicit proposed concurrency detail, not a new approval bypass.
- MCP definitions use local `$ref` files for design reuse. Resolve/bundle them before publishing schemas to a live client; clients cannot fetch this machine's relative design files.

## Check the Contracts

Use the Python environment described in the installed AgentBuild skill's `references/contracts-and-examples.md`:

```sh
~/.codex/venvs/agentbuild-contracts/bin/python ~/.codex/skills/agentbuild/scripts/validate_contracts.py --project projects/agentboard
```

Checks include OpenAPI structure, JSON Schema definitions, local references, UUID/date-time formats, registered examples, actual REST/MCP binding and complete MCP example coverage. These are static checks, not tests of authorization, database transactions or client interoperability.

References: [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) · [MCP tool schemas](https://modelcontextprotocol.io/specification/2025-06-18/server/tools). Protocol version selection remains subject to the [client compatibility gate](../mcp-tools.md).

## Output Consistency Gate

```sh
~/.codex/venvs/agentbuild-contracts/bin/python ~/.codex/skills/agentbuild/scripts/sync_navigation.py --project projects/agentboard --write
~/.codex/venvs/agentbuild-contracts/bin/python ~/.codex/skills/agentbuild/scripts/check_outputs.py --project projects/agentboard --strict
```

Navigation tables are derived from story files, tool schemas and example bindings. Only explicitly marked rows are rewritten. Required update-ticket outcomes and selected HTTP cases are declared in the contracts; removing their examples fails validation. The gate is read-only and does not prove runtime behavior.
