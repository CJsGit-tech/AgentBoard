---
name: "Risks and References"
description: "Identify what still needs evidence before implementation claims or release."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:authorization", "concern:auditability", "concern:data-integrity", "concern:retention", "concern:privacy", "concern:reliability", "concern:compatibility", "concern:security"]
---

# Risks and References

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Identify what still needs evidence before implementation claims or release.

## Open Risks & Decisions

| Owner | Verify / resolve |
| --- | --- |
| Solution Architect | Exact SDK/protocol and image versions; host matrix; resource budgets; schema performance |
| Integration implementer | Per-client MCP/approval behavior; some clients may support only Create/Read until adapters work |
| Operator / architect | Backup timing and tested restore; clarify stricter physical erasure if needed |
| Designer | Logging filters, document comparisons and separate task/approval indicators |

**Rule:** Never weaken approval to claim client compatibility. The confirmed brief permits drafting; it does not establish tested runtime behavior.

The concise Product Vision and story feature links remain unchanged. No hosted/paid providers were introduced.

## Official References

Retained from the prior draft; consulted 2026-11-17, not reverified during this presentation-only revision.

| Reference | Use |
| --- | --- |
| [MCP transports](https://modelcontextprotocol.io/specification/latest/basic/transports) | Choose versions supported by actual clients |
| [MCP elicitation](https://modelcontextprotocol.io/specification/latest/client/elicitation) | Capability-dependent user interaction, not universal approval UI |
| [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk) | Pin and test release |
| [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/) | Readiness and completed-job conditions |
| [Postgres pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html) | Consistent export and recovery formats |
