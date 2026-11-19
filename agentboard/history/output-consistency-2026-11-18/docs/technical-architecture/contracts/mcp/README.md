# MCP Tool Contracts

Pick a tool, then open only its schema and the desired input/output example. These JSON files describe draft tools, not a running MCP server.

| Tool | Permission | Input/output schema | Input example | Output example |
| --- | --- | --- | --- | --- |
| `list_projects` | read | [Schema](list-projects.schema.json) | [Input](../../examples/mcp/list-projects.input.json) | [Output](../../examples/mcp/list-projects.output.json) |
| `get_project` | read | [Schema](get-project.schema.json) | [Input](../../examples/mcp/get-project.input.json) | [Output](../../examples/mcp/get-project.output.json) |
| `create_project` | create | [Schema](create-project.schema.json) | [Input](../../examples/mcp/create-project.input.json) | [Output](../../examples/mcp/create-project.output.json) |
| `update_project` | approval_required | [Schema](update-project.schema.json) | [Input](../../examples/mcp/update-project.input.json) | [Output](../../examples/mcp/update-project.output.json) |
| `delete_project` | approval_required | [Schema](delete-project.schema.json) | [Input](../../examples/mcp/delete-project.input.json) | [Output](../../examples/mcp/delete-project.output.json) |
| `list_roles` | read | [Schema](list-roles.schema.json) | [Input](../../examples/mcp/list-roles.input.json) | [Output](../../examples/mcp/list-roles.output.json) |
| `get_role` | read | [Schema](get-role.schema.json) | [Input](../../examples/mcp/get-role.input.json) | [Output](../../examples/mcp/get-role.output.json) |
| `create_role` | create | [Schema](create-role.schema.json) | [Input](../../examples/mcp/create-role.input.json) | [Output](../../examples/mcp/create-role.output.json) |
| `update_role` | approval_required | [Schema](update-role.schema.json) | [Input](../../examples/mcp/update-role.input.json) | [Output](../../examples/mcp/update-role.output.json) |
| `delete_role` | approval_required | [Schema](delete-role.schema.json) | [Input](../../examples/mcp/delete-role.input.json) | [Output](../../examples/mcp/delete-role.output.json) |
| `list_tickets` | read | [Schema](list-tickets.schema.json) | [Input](../../examples/mcp/list-tickets.input.json) | [Output](../../examples/mcp/list-tickets.output.json) |
| `get_ticket` | read | [Schema](get-ticket.schema.json) | [Input](../../examples/mcp/get-ticket.input.json) | [Output](../../examples/mcp/get-ticket.output.json) |
| `create_ticket` | create | [Schema](create-ticket.schema.json) | [Input](../../examples/mcp/create-ticket.input.json) | [Output](../../examples/mcp/create-ticket.output.json) |
| `update_ticket` | approval_required | [Schema](update-ticket.schema.json) | [Input](../../examples/mcp/update-ticket.input.json) | [Output](../../examples/mcp/update-ticket.output.json) |
| `delete_ticket` | approval_required | [Schema](delete-ticket.schema.json) | [Input](../../examples/mcp/delete-ticket.input.json) | [Output](../../examples/mcp/delete-ticket.output.json) |
| `list_documents` | read | [Schema](list-documents.schema.json) | [Input](../../examples/mcp/list-documents.input.json) | [Output](../../examples/mcp/list-documents.output.json) |
| `get_document` | read | [Schema](get-document.schema.json) | [Input](../../examples/mcp/get-document.input.json) | [Output](../../examples/mcp/get-document.output.json) |
| `create_document` | create | [Schema](create-document.schema.json) | [Input](../../examples/mcp/create-document.input.json) | [Output](../../examples/mcp/create-document.output.json) |
| `update_document` | approval_required | [Schema](update-document.schema.json) | [Input](../../examples/mcp/update-document.input.json) | [Output](../../examples/mcp/update-document.output.json) |
| `delete_document` | approval_required | [Schema](delete-document.schema.json) | [Input](../../examples/mcp/delete-document.input.json) | [Output](../../examples/mcp/delete-document.output.json) |
| `list_document_versions` | read | [Schema](list-document-versions.schema.json) | [Input](../../examples/mcp/list-document-versions.input.json) | [Output](../../examples/mcp/list-document-versions.output.json) |
| `get_document_version` | read | [Schema](get-document-version.schema.json) | [Input](../../examples/mcp/get-document-version.input.json) | [Output](../../examples/mcp/get-document-version.output.json) |
| `compare_document_versions` | read | [Schema](compare-document-versions.schema.json) | [Input](../../examples/mcp/compare-document-versions.input.json) | [Output](../../examples/mcp/compare-document-versions.output.json) |
| `restore_document_version` | approval_required | [Schema](restore-document-version.schema.json) | [Input](../../examples/mcp/restore-document-version.input.json) | [Output](../../examples/mcp/restore-document-version.output.json) |
| `link_document` | create | [Schema](link-document.schema.json) | [Input](../../examples/mcp/link-document.input.json) | [Output](../../examples/mcp/link-document.output.json) |
| `unlink_document` | approval_required | [Schema](unlink-document.schema.json) | [Input](../../examples/mcp/unlink-document.input.json) | [Output](../../examples/mcp/unlink-document.output.json) |
| `append_activity` | create | [Schema](append-activity.schema.json) | [Input](../../examples/mcp/append-activity.input.json) | [Output](../../examples/mcp/append-activity.output.json) |
| `list_activity` | read | [Schema](list-activity.schema.json) | [Input](../../examples/mcp/list-activity.input.json) | [Output](../../examples/mcp/list-activity.output.json) |
| `get_project_progress` | read | [Schema](get-project-progress.schema.json) | [Input](../../examples/mcp/get-project-progress.input.json) | [Output](../../examples/mcp/get-project-progress.output.json) |
| `get_mutation_request` | read | [Schema](get-mutation-request.schema.json) | [Input](../../examples/mcp/get-mutation-request.input.json) | [Output](../../examples/mcp/get-mutation-request.output.json) |
| `retry_mutation_request` | approval_required | [Schema](retry-mutation-request.schema.json) | [Input](../../examples/mcp/retry-mutation-request.input.json) | [Output](../../examples/mcp/retry-mutation-request.output.json) |

Update ticket additional outcomes: [applied](../../examples/mcp/update-ticket.applied.json) · [rejected](../../examples/mcp/update-ticket.rejected.json) · [revision conflict](../../examples/mcp/update-ticket.conflict.json).

Read outputs are application `structuredContent` payloads; they omit JSON-RPC/MCP transport envelopes. The running server must emit the proper protocol result wrapper. Tool annotations are descriptive hints, not approval enforcement.

[Approval policy](../../approval-flow.md) · [Catalog JSON](tools.json) · [All contracts](../README.md)
