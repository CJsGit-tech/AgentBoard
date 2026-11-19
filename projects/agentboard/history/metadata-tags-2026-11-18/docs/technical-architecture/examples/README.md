# AgentBoard JSON Examples

**Purpose:** Open one example when a schema's shape is unclear.

| Representation | Examples |
| --- | --- |
| Persisted records | [Ticket](data/ticket.record.json) · [Mutation request](data/mutation-request.record.json) · [Document version](data/document-version.record.json) |
| Browser HTTP JSON bodies | [Request/response index](api/README.md) |
| MCP application payloads | [Pick a tool](../contracts/mcp/README.md) |

- UUIDs and names are fictional; no tokens, secrets or production data are included.
- Examples are standalone snapshots, not a single ordered transaction timeline.
- API files contain JSON bodies only. Authentication, CSRF, path/query parameters, headers and status codes are defined by OpenAPI.
- MCP input files are tool arguments; output files are application structured payloads, not transport envelopes.
- `applied: false` on approval-required output means no business mutation occurred. A later applied example represents verified approval followed by a successful revision check.
- The [manifest](../contracts/manifest.json) binds each example to its actual schema/operation/tool. Update schema and examples together; validate before reporting completion.
