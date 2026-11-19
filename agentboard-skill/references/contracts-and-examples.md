# Technical contracts and schema-bound JSON examples

## Structure and authority

Keep interface detail inside technical-architecture, separate from concise explanations:

```text
technical-architecture/
  README.md
  data-model.md
  api-integrations.md           # existing projects may use api-contracts.md
  mcp-tools.md                  # when MCP applies
  contracts/
    README.md
    manifest.json
    openapi.json                # OpenAPI 3.1 JSON when HTTP APIs apply
    schemas/domain.schema.json  # shared fields; distinguish records/read projections
    mcp/
      README.md
      tools.json
      update-ticket.schema.json
  examples/
    README.md
    data/ticket.record.json
    api/create-ticket.request.json
    api/create-ticket.response.json
    mcp/update-ticket.input.json
    mcp/update-ticket.output.json
```

These are ordinary files; no context database, snapshots or generated combined exports. Markdown explains rationale, policies and reading paths. Schemas are authoritative for field shapes/types and interface outcomes. Examples illustrate those schemas and must not invent an independent contract. Transactional invariants, authorization enforcement, database foreign keys and integration behavior still require implementation tests and semantic review.

Use a few representative data records where they explain ambiguity. Define REST boundaries in OpenAPI when present, and input/output schemas for every exposed MCP tool. Each MCP tool needs an input and output example. Include success and important error/approval outcomes for representative workflows. Label examples as persisted records, read projections, HTTP JSON bodies or MCP application payloads; do not mix them with transport envelopes. Use realistic UUIDs/times and fictional values, never secrets or production content.

Keep one field-definition source and use local `$ref` reuse. MCP design refs may need resolution/bundling before a live server advertises them. Do not assume clients can retrieve local schema files. Tool annotations describe behavior; they do not enforce approval.

## Discovery and skeletons

During the confirmed architecture plan, determine applicability of HTTP, MCP and persisted data. The scaffold script creates contracts/examples README skeletons and an unfinished manifest, not invented endpoints or tool definitions. Fill scope with explicit applicability/reasons from requirements. If an area is not applicable, explain why and do not create fake APIs or schemas. Unfinished scopes/markers fail readiness checks.

Do not migrate unrelated existing topics simply to add contracts. For an existing project, preserve topic files and add contracts/examples plus concise reading links. Exact wire spellings and limits not previously decided must be labeled draft proposals; do not misrepresent them as approved product decisions.

## Manifest format

`contracts/manifest.json` is a lightweight validation inventory, not a source store:

```json
{
  "schema_version": 1,
  "status": "draft",
  "scope": {
    "rest": {"applicable": true, "reason": "Browser API"},
    "mcp": {"applicable": true, "reason": "Agents operate the app"},
    "data": {"applicable": true, "reason": "Persisted domain records"}
  },
  "openapi": "contracts/openapi.json",
  "mcp_catalog": "contracts/mcp/tools.json",
  "schemas": ["contracts/schemas/domain.schema.json", "contracts/mcp/update-ticket.schema.json"],
  "examples": [
    {"path": "examples/data/ticket.record.json", "kind": "data", "schema": "contracts/schemas/domain.schema.json#/$defs/TicketRecord"},
    {"path": "examples/api/create-ticket.request.json", "kind": "rest-request", "operation_id": "create_ticket"},
    {"path": "examples/api/create-ticket.response.json", "kind": "rest-response", "operation_id": "create_ticket", "status": "201"},
    {"path": "examples/mcp/update-ticket.input.json", "kind": "mcp-input", "tool": "update_ticket"},
    {"path": "examples/mcp/update-ticket.output.json", "kind": "mcp-output", "tool": "update_ticket"}
  ]
}
```

This is an illustrative inventory: fill all schemas/tools/examples it refers to. A nonapplicable scope uses `applicable: false` with reason and a null openapi/mcp_catalog path where relevant. All JSON contract/example files must be inventoried; README navigation remains human-readable. The catalog is `{ "tools": [{ "name": "...", "inputSchema": {...}, "outputSchema": {...}, "x-agentbuild-permission": "read|create|approval_required" }] }`.

REST example schemas are taken from the actual operation's JSON request body or specified response status. MCP examples are checked against the named tool's declared input/output schema. Avoid pointing an example at an unrelated permissive schema simply to make it pass. A 204 HTTP response has no JSON body; SSE examples/transport envelopes are documented separately.

## Validation environment

Use standard JSON Schema/OpenAPI validators, not a partial hand-written schema engine. Python >=3.10 is required. Install isolated dependencies explicitly; no script downloads packages during validation:

```sh
python3 -m venv <project-path>/.venv-agentbuild
<project-path>/.venv-agentbuild/bin/python -m pip install -r <skill-root>/requirements-contracts.txt
<project-path>/.venv-agentbuild/bin/python <skill-root>/scripts/validate_contracts.py --project <project-path>
<project-path>/.venv-agentbuild/bin/python <skill-root>/scripts/validate_project.py --project <project-path>
```

Project validation invokes these checks when a contract manifest exists; profile-based architecture validation requires the scaffold manifest to be resolved. Without required packages it reports an actionable error, not a pass. Legacy folders with no contract manifest retain their existing validation behavior until the user requests an upgrade.

Checks cover OpenAPI 3.1 structure; JSON Schema 2020-12 syntax; local references/paths; UUID/date-time formats; schema-bound examples; complete MCP input/output example coverage; applicability decisions; unregistered JSON files; unfinished markers and symlinks. References must stay within technical-architecture; validation is offline. Only JSON contract files and local JSON Pointers are supported by this helper. YAML or other schema dialects require an explicit compatible validator rather than silently treating them as JSON.

Structural success does not prove semantic correctness, authorization, cross-record relationships, aggregate counts, byte-size limits, runtime API conformance or MCP client support. Review those separately. Render/check diagrams and preserve the minimal-reading topic design: short explanation first, linked exact contract/example detail when needed.

## Change workflow

On interface changes, edit the authoritative schema, update bound examples, review Markdown policy/links, and run both validators. Preserve prior versions and update manifest artifact metadata using the existing plain-folder workflow. Do not change unrelated story/diagram content to make examples pass. Contracts remain drafts until approved; matching examples do not automatically approve a design.

## Completion consistency

Follow output-consistency.md. Use sync_navigation.py for explicitly marked story/MCP navigation blocks and check_outputs.py --strict for one read-only gate. Derive indexes from canonical sources, declare important example outcomes/statuses, and keep semantic review separate.
