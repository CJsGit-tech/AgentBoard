---
name: "Architectural decision records"
description: "Find a decision and its rationale by stable ADR ID."
kind: "architecture-topic"
tags: ["feature:product-project-management", "feature:agent-role-management", "feature:task-coordination", "feature:document-management", "feature:progress-tracking", "concern:authorization", "concern:auditability", "concern:data-integrity", "concern:retention", "concern:privacy", "concern:compatibility"]
---

# Architectural decision records

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Find a decision and its rationale by stable ADR ID.

## Architectural Decisions

| ID | Decision | Rationale / revision | Related stories |
| --- | --- | --- | --- |
| ADR-001 | Local web app via Docker Compose | Confirmed, single personal-computer deployment | US-001–015 |
| ADR-002 | Separate web/backend/db with helper jobs | Revises previous combined-container proposal for module clarity and shared browser/MCP backend | US-001–015 |
| ADR-003 | Local Postgres | Supersedes SQLite proposal after explicit owner selection | US-001–015 |
| ADR-004 | External agents operate through MCP and report activity | Replaces manual-only integration boundary; no process management | US-003, US-005, US-011–013 |
| ADR-005 | Revision checks plus atomic audit writes | Preserves previous concurrency decision; extends to approvals | US-006–007, US-010–012, US-015 |
| ADR-006 | Project-scoped APIs and database constraints | Preserves project isolation | US-002, US-005, US-008–009, US-011 |
| ADR-007 | Client approval for U/D; separate badge | Confirmed; unsupported approval does not mutate | US-012 |
| ADR-008 | Minimal labeled activity, live SSE, 30-day expiry | Confirmed behavior; SSE/maintenance mechanism proposed | US-010, US-013–014 |
| ADR-009 | Current plus three prior document versions | Confirmed; agent-readable history and approved restore | US-007, US-015 |

**Status:** Preserve ADR IDs. [Constraints](constraints.md) identifies confirmed requirements; library/service choices remain proposals. The document remains a draft.
