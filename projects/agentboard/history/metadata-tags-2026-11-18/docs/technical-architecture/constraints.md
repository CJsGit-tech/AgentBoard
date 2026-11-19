# Environment and Constraints

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Separate agreed requirements from implementation proposals.

## Environment & Constraints

| Concern | Confirmed requirement |
| --- | --- |
| Deployment | Personal computer only; Docker Compose; one builder |
| Stack | React/Vite; Python FastAPI; local Postgres |
| Providers | No hosted database, identity, storage or deployment provider; model access stays with Codex/Claude |
| Agent role | External clients manage records/report work; AgentBoard does not control processes |
| Permission | Agent Create/Read free after connection authorization; Update/Delete through verified client approval |
| UI | Separate Needs approval badge; live labeled activity |
| Retention | 30-day logs; current document plus three previous versions; agent-readable history |
| Offline boundary | Core local app works after installation; independent agents may require connectivity |

## Proposed Baseline

| Choice | Verification needed |
| --- | --- |
| Separate services, SQLAlchemy/psycopg/Alembic, SSE | Build and integration tests |
| Transport bridge, exact ports, cleanup cadence, concurrency controls | Target-client and runtime tests |
| Desktop browser; validate macOS arm64 first | Agree supported host/browser matrix before claiming support |
| 100 projects, 10,000 tickets, 1,000 documents, 10 MCP connections | Benchmark envelope, not proven capacity |

## Evidence Status

Multiple discovery rounds and the final brief established the confirmed requirements. The owner authorized this architecture and FastAPI choice. That does not approve every implementation proposal or prove it works.

Exact package/image versions and client capability matrix remain **unverified**. Pin supported versions during implementation and negotiate a tested common MCP protocol version.

[Decisions](decisions.md) · [Verification backlog](risks-and-references.md)
