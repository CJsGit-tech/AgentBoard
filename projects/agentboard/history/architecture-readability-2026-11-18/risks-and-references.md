# Open risks and official sources

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## 12. Open Risks & Decisions

Implementation verification: client-specific MCP capability/approval tests may reveal that some targets support only CR until adapters are available; never weaken approval to claim compatibility. Owner-approved brief is sufficient to author this draft; exact SDK protocol versions, image versions, host matrix, backup timing, resource budgets, and schema performance remain implementation validation tasks. Design Profile must show logging filters, document comparisons and separate task/approval indicators.

Project Vision is intentionally concise and unchanged by this request. New stories trace MCP/approvals/logging/history to its existing role, task, document and progress features. No hosted services or paid provider integrations were introduced.

Official references consulted 2026-11-17:

- [MCP transports](https://modelcontextprotocol.io/specification/latest/basic/transports) — stdio and Streamable HTTP bindings; verify against the version selected for clients.
- [MCP elicitation](https://modelcontextprotocol.io/specification/latest/client/elicitation) — user interaction and negotiated client support; does not guarantee every client's approval UI.
- [Official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk) — pin and test a supported release.
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/) — health and completed-job conditions.
- [Postgres pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html) — consistent database export and restore formats.
