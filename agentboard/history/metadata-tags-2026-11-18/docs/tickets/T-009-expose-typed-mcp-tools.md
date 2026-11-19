# T-009 — Expose shared services as typed MCP tools

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-002, T-004, T-005, T-006, T-007, T-008, T-018
Estimate (days): 3
Estimate scope: Build
Estimate basis: Provisional: 31 documented tool bindings reuse service tests; discovery/transport integration tests and review included, real-client matrix separate.

## Outcome
Authorized independent agents discover and call typed AgentBoard tools without a second business-logic path.

## Acceptance Criteria
- Implement the cataloged project/role/ticket/document/history/activity/progress/request tools on shared services and validated input/output schemas.
- Provide authenticated loopback transport with negotiated protocol and test-selected SDK versions; preserve request identity and cancellation.
- Keep Create/Read available without per-operation approval; route all updates, unlinking, restores and deletions through the verified approval gate.
- Test retry-safe create/report calls, project isolation and structured failure results; reconcile tool schemas/examples with the implemented planning fields before publication.

## Context
- [US-011](../user-stories/US-011-operate-agentboard-through-mcp.md)
- [US-012](../user-stories/US-012-approve-agent-updates-and-deletions-in-the-client.md)
- [US-013](../user-stories/US-013-report-and-review-agent-activity.md)
- [US-015](../user-stories/US-015-read-compare-and-restore-document-revisions.md)
- [mcp-tools](../technical-architecture/mcp-tools.md)
- [approval-flow](../technical-architecture/approval-flow.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-002](T-002-persist-projects-and-agent-roles.md)
- [T-004](T-004-persist-tickets-and-progress.md)
- [T-005](T-005-persist-documents-and-bounded-revisions.md)
- [T-006](T-006-persist-ticket-document-links.md)
- [T-007](T-007-record-filter-and-expire-activity.md)
- [T-008](T-008-enforce-client-approved-mutations.md)
- [T-018](T-018-persist-ticket-classification-and-estimates.md)
