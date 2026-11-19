# MCP Tool Contracts

Pick a tool, then open only its schema and the desired input/output example. These JSON files describe draft tools, not a running MCP server.

<!-- agentbuild:mcp-tools:start -->
| Tool | Permission | Input/output schema | Input example | Output examples |
| --- | --- | --- | --- | --- |
| `append_activity` | create | [Input](append-activity.schema.json#/$defs/input) · [Output](append-activity.schema.json#/$defs/output) | [input](../../examples/mcp/append-activity.input.json) | [output](../../examples/mcp/append-activity.output.json) |
| `compare_document_versions` | read | [Input](compare-document-versions.schema.json#/$defs/input) · [Output](compare-document-versions.schema.json#/$defs/output) | [input](../../examples/mcp/compare-document-versions.input.json) | [output](../../examples/mcp/compare-document-versions.output.json) |
| `create_document` | create | [Input](create-document.schema.json#/$defs/input) · [Output](create-document.schema.json#/$defs/output) | [input](../../examples/mcp/create-document.input.json) | [output](../../examples/mcp/create-document.output.json) |
| `create_project` | create | [Input](create-project.schema.json#/$defs/input) · [Output](create-project.schema.json#/$defs/output) | [input](../../examples/mcp/create-project.input.json) | [output](../../examples/mcp/create-project.output.json) |
| `create_role` | create | [Input](create-role.schema.json#/$defs/input) · [Output](create-role.schema.json#/$defs/output) | [input](../../examples/mcp/create-role.input.json) | [output](../../examples/mcp/create-role.output.json) |
| `create_ticket` | create | [Input](create-ticket.schema.json#/$defs/input) · [Output](create-ticket.schema.json#/$defs/output) | [input](../../examples/mcp/create-ticket.input.json) | [output](../../examples/mcp/create-ticket.output.json) |
| `delete_document` | approval_required | [Input](delete-document.schema.json#/$defs/input) · [Output](delete-document.schema.json#/$defs/output) | [input](../../examples/mcp/delete-document.input.json) | [output](../../examples/mcp/delete-document.output.json) |
| `delete_project` | approval_required | [Input](delete-project.schema.json#/$defs/input) · [Output](delete-project.schema.json#/$defs/output) | [input](../../examples/mcp/delete-project.input.json) | [output](../../examples/mcp/delete-project.output.json) |
| `delete_role` | approval_required | [Input](delete-role.schema.json#/$defs/input) · [Output](delete-role.schema.json#/$defs/output) | [input](../../examples/mcp/delete-role.input.json) | [output](../../examples/mcp/delete-role.output.json) |
| `delete_ticket` | approval_required | [Input](delete-ticket.schema.json#/$defs/input) · [Output](delete-ticket.schema.json#/$defs/output) | [input](../../examples/mcp/delete-ticket.input.json) | [output](../../examples/mcp/delete-ticket.output.json) |
| `get_document` | read | [Input](get-document.schema.json#/$defs/input) · [Output](get-document.schema.json#/$defs/output) | [input](../../examples/mcp/get-document.input.json) | [output](../../examples/mcp/get-document.output.json) |
| `get_document_version` | read | [Input](get-document-version.schema.json#/$defs/input) · [Output](get-document-version.schema.json#/$defs/output) | [input](../../examples/mcp/get-document-version.input.json) | [output](../../examples/mcp/get-document-version.output.json) |
| `get_mutation_request` | read | [Input](get-mutation-request.schema.json#/$defs/input) · [Output](get-mutation-request.schema.json#/$defs/output) | [input](../../examples/mcp/get-mutation-request.input.json) | [output](../../examples/mcp/get-mutation-request.output.json) |
| `get_project` | read | [Input](get-project.schema.json#/$defs/input) · [Output](get-project.schema.json#/$defs/output) | [input](../../examples/mcp/get-project.input.json) | [output](../../examples/mcp/get-project.output.json) |
| `get_project_progress` | read | [Input](get-project-progress.schema.json#/$defs/input) · [Output](get-project-progress.schema.json#/$defs/output) | [input](../../examples/mcp/get-project-progress.input.json) | [output](../../examples/mcp/get-project-progress.output.json) |
| `get_role` | read | [Input](get-role.schema.json#/$defs/input) · [Output](get-role.schema.json#/$defs/output) | [input](../../examples/mcp/get-role.input.json) | [output](../../examples/mcp/get-role.output.json) |
| `get_ticket` | read | [Input](get-ticket.schema.json#/$defs/input) · [Output](get-ticket.schema.json#/$defs/output) | [input](../../examples/mcp/get-ticket.input.json) | [output](../../examples/mcp/get-ticket.output.json) |
| `link_document` | create | [Input](link-document.schema.json#/$defs/input) · [Output](link-document.schema.json#/$defs/output) | [input](../../examples/mcp/link-document.input.json) | [output](../../examples/mcp/link-document.output.json) |
| `list_activity` | read | [Input](list-activity.schema.json#/$defs/input) · [Output](list-activity.schema.json#/$defs/output) | [input](../../examples/mcp/list-activity.input.json) | [output](../../examples/mcp/list-activity.output.json) |
| `list_document_versions` | read | [Input](list-document-versions.schema.json#/$defs/input) · [Output](list-document-versions.schema.json#/$defs/output) | [input](../../examples/mcp/list-document-versions.input.json) | [output](../../examples/mcp/list-document-versions.output.json) |
| `list_documents` | read | [Input](list-documents.schema.json#/$defs/input) · [Output](list-documents.schema.json#/$defs/output) | [input](../../examples/mcp/list-documents.input.json) | [output](../../examples/mcp/list-documents.output.json) |
| `list_projects` | read | [Input](list-projects.schema.json#/$defs/input) · [Output](list-projects.schema.json#/$defs/output) | [input](../../examples/mcp/list-projects.input.json) | [output](../../examples/mcp/list-projects.output.json) |
| `list_roles` | read | [Input](list-roles.schema.json#/$defs/input) · [Output](list-roles.schema.json#/$defs/output) | [input](../../examples/mcp/list-roles.input.json) | [output](../../examples/mcp/list-roles.output.json) |
| `list_tickets` | read | [Input](list-tickets.schema.json#/$defs/input) · [Output](list-tickets.schema.json#/$defs/output) | [input](../../examples/mcp/list-tickets.input.json) | [output](../../examples/mcp/list-tickets.output.json) |
| `restore_document_version` | approval_required | [Input](restore-document-version.schema.json#/$defs/input) · [Output](restore-document-version.schema.json#/$defs/output) | [input](../../examples/mcp/restore-document-version.input.json) | [output](../../examples/mcp/restore-document-version.output.json) |
| `retry_mutation_request` | approval_required | [Input](retry-mutation-request.schema.json#/$defs/input) · [Output](retry-mutation-request.schema.json#/$defs/output) | [input](../../examples/mcp/retry-mutation-request.input.json) | [output](../../examples/mcp/retry-mutation-request.output.json) |
| `unlink_document` | approval_required | [Input](unlink-document.schema.json#/$defs/input) · [Output](unlink-document.schema.json#/$defs/output) | [input](../../examples/mcp/unlink-document.input.json) | [output](../../examples/mcp/unlink-document.output.json) |
| `update_document` | approval_required | [Input](update-document.schema.json#/$defs/input) · [Output](update-document.schema.json#/$defs/output) | [input](../../examples/mcp/update-document.input.json) | [output](../../examples/mcp/update-document.output.json) |
| `update_project` | approval_required | [Input](update-project.schema.json#/$defs/input) · [Output](update-project.schema.json#/$defs/output) | [input](../../examples/mcp/update-project.input.json) | [output](../../examples/mcp/update-project.output.json) |
| `update_role` | approval_required | [Input](update-role.schema.json#/$defs/input) · [Output](update-role.schema.json#/$defs/output) | [input](../../examples/mcp/update-role.input.json) | [output](../../examples/mcp/update-role.output.json) |
| `update_ticket` | approval_required | [Input](update-ticket.schema.json#/$defs/input) · [Output](update-ticket.schema.json#/$defs/output) | [input](../../examples/mcp/update-ticket.input.json) | [applied](../../examples/mcp/update-ticket.applied.json) · [conflict](../../examples/mcp/update-ticket.conflict.json) · [output](../../examples/mcp/update-ticket.output.json) · [rejected](../../examples/mcp/update-ticket.rejected.json) |
<!-- agentbuild:mcp-tools:end -->

Update ticket additional outcomes: [applied](../../examples/mcp/update-ticket.applied.json) · [rejected](../../examples/mcp/update-ticket.rejected.json) · [revision conflict](../../examples/mcp/update-ticket.conflict.json).

Read outputs are application `structuredContent` payloads; they omit JSON-RPC/MCP transport envelopes. The running server must emit the proper protocol result wrapper. Tool annotations are descriptive hints, not approval enforcement.

[Approval policy](../../approval-flow.md) · [Catalog JSON](tools.json) · [All contracts](../README.md)
