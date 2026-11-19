# Technology stack and tradeoffs

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## 4. Technology & SDK Decisions

| Layer | Selection | Pros / reason | Cons / alternative |
| --- | --- | --- | --- |
| UI | React, TypeScript, Vite | Confirmed preference; reusable editors and board modules | SPA state/error handling needed; server templates simpler for small forms |
| API | FastAPI, Pydantic, Uvicorn | Confirmed; typed contracts, Python MCP integration boundary | Requires deliberate lifecycle/streaming coordination; Django offers more built-in administration |
| MCP | Official Python MCP SDK, pinned to tested release | Standard tool schemas and negotiated client capabilities | Client/version differences require adapters and integration tests; tool annotations alone do not enforce approval |
| Persistence | Postgres, SQLAlchemy, psycopg, Alembic | Confirmed database; transactional approval/revision/event writes and concurrency | More RAM, startup, and backup work than SQLite; accepted tradeoff after owner discussion |
| Live UI | SSE with persisted event IDs | One-way live updates fit the activity board; reconnectable HTTP | Proxy buffering/timeouts require testing; WebSocket unnecessary until bidirectional requirements emerge |
| Local delivery | Separate web, backend, db; maintenance and migration helpers | Explicit module/container boundaries and repeatable lifecycle | More containers than the superseded embedded design |

React/Vite, FastAPI, and Postgres are selected; exact versions and dependency interoperability remain unverified. SDK support for elicitation must be checked against the negotiated protocol/client capabilities, not inferred from the existence of MCP tools. Official references are listed at the end.
