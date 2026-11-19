# HTTP JSON Body Examples

| Scenario | Request | Response |
| --- | --- | --- |
| Create ticket | [Body](create-ticket.request.json) | [201 body](create-ticket.response.json) |
| Update ticket | [Body](update-ticket.request.json) | [409 conflict](update-ticket.conflict.json) |
| Project progress | GET; no body | [200 body](project-progress.response.json) |

Use the [OpenAPI contract](../../contracts/openapi.json) for required local session/CSRF, idempotency header, UUID path parameters and response status. A 204 response has no JSON body. `/events` is an SSE stream; it is not a JSON resource under `/api/v1`.
