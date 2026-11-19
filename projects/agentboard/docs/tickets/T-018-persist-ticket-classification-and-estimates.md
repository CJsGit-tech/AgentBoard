---
name: "T-018 — Persist ticket classification, estimates and planning data"
description: "AgentBoard can store/query FE/BE, BUG/BUILD and day estimates as required by the latest ticket-planning decisions."
kind: "ticket"
tags: ["feature:task-coordination", "feature:progress-tracking", "concern:data-integrity"]
---

# T-018 — Persist ticket classification, estimates and planning data

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-004
Estimate (days): 2.5
Estimate scope: Build
Estimate basis: Provisional/high uncertainty: metadata storage/contracts and tests/review included; advanced scheduling is excluded pending a confirmed planning policy.

## Outcome
AgentBoard can store/query FE/BE, BUG/BUILD and day estimates as required by the latest ticket-planning decisions.

## Acceptance Criteria
- Propose and reconcile a shared data/REST/MCP contract for execution role, work type, positive day estimate, estimate scope/basis and ticket dependencies; update affected draft schemas/examples/topics together before implementation.
- Keep FE/BE routing distinct from existing self/role/unassigned ownership and Needs approval; preserve existing domain status semantics and existing records during migration.
- Persist/query the agreed fields and enforce nonnegative/positive bounds as appropriate, valid same-project dependencies and no cycles; unestimated repair is unknown, not zero.
- Provide planning inputs/effort summaries for timeline tracking, distinguishing effort from calendar duration. Calendar/capacity/forecast policy and date fields require explicit confirmation; record the decision before adding a scheduling algorithm.
- Test migrations/defaults for existing tickets, validation, request idempotency and schema/example compatibility; protect agent field updates through the same mutation gate.

## Context
- Latest user decisions in this conversation (2026-11-18): FE/BE routing, BUG/BUILD classification, per-ticket estimates in days, and AgentBoard timeline/estimate tracking. Existing schemas/screens do not yet cover this extension; detailed scheduling behavior remains to be confirmed.
- [data-model](../technical-architecture/data-model.md)
- [api-contracts](../technical-architecture/api-contracts.md)
- [mcp-tools](../technical-architecture/mcp-tools.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-004](T-004-persist-tickets-and-progress.md)
