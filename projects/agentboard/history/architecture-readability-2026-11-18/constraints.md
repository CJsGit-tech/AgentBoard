# Environment and discovery

> Owner: Solution Architect | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-17

## Discovery Record

Multiple discovery rounds established local-only deployment, a single builder, React/Vite, Python, Postgres, and no hosted infrastructure providers. The owner confirmed FastAPI and authorized this revision after reviewing the complete brief. External model access stays with Codex/Claude. Agents may Create/Read without per-operation approval; Update/Delete require approval through the client interface. Unsupported approval must not execute changes. Tickets show a separate Needs approval badge. Logs are minimal, labeled, live, and retained for 30 days. Documents live in Postgres with a current version plus three previous versions, accessible to agents.

Proposed implementation details below include service separation, transport adapters, SQLAlchemy/Alembic, SSE, exact ports, cleanup cadence, and concurrency controls. These refine the brief and require implementation verification, rather than representing tested software.

## 2. Environment & Constraints

| Area | Constraint / decision | Status |
| --- | --- | --- |
| Deployment | Personal computer only; Docker Compose; one user | Confirmed |
| Frontend / backend / database | React + Vite / Python FastAPI / local Postgres | Confirmed |
| Agent clients | Codex desktop, Codex CLI, Claude Code, Claude Desktop | Required compatibility targets, not yet tested |
| Providers | No hosted database, identity, storage, or deployment service | Confirmed |
| Host / browsers | Desktop browser; validate macOS arm64 first, then other claimed targets | Proposed validation order |
| Agent lifecycle | External; only MCP operations and activity reporting | Confirmed |
| Offline use | Core app works after local installation without internet; external agents may need their own connectivity | Design requirement |
| Capacity | Initial test envelope: 100 projects, 10,000 tickets, 1,000 documents; 10 concurrent MCP connections | Proposed benchmark envelope |

No installed library versions or client capability matrix have been verified. Pin supported package/image versions during implementation; negotiate a tested common MCP protocol version rather than assume all clients support the newest specification.
