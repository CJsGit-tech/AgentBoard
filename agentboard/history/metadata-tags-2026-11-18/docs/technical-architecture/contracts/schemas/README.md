# Shared Domain Schemas

[domain.schema.json](domain.schema.json) is the shared field definition source for REST, MCP and data examples.

| Definition | Representation |
| --- | --- |
| TicketRecord | Persisted ticket; no derived approval badge |
| TicketView | API/MCP read projection; includes derived `needs_approval` |
| MutationRequest | Pending/terminal request metadata and exact proposed change |
| DocumentVersion | One immutable retained content version |
| Project, Role, Document, TicketDocument, ActivityEvent | Domain records |
| Create / Changes / Update, Page, Progress, Error | Interface-specific shapes |

Read projection shapes are not SQL table definitions. Services enforce project foreign keys, approved revision binding, retention counts, timestamp order and aggregate counts. Examples do not replace those tests.
