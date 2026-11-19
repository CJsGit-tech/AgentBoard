# T-003 — Authorize local browser and agent clients

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-001
Estimate (days): 2.5
Estimate scope: Build
Estimate basis: Provisional: local credential/session boundary, abuse-case tests and review; client-specific approval adapters are separate.

## Outcome
Local access is authorized without hosted identity, and agent credentials cannot impersonate human browser actions.

## Acceptance Criteria
- Implement local first-run pairing/session establishment and separate scoped MCP client credentials; document setup and revoke/reconnect behavior.
- Enforce Host/Origin, browser CSRF, request size/content type and project boundaries at appropriate entry points.
- Store secrets outside frontend assets and redact them from operational/activity logs.
- Test unauthorized calls, forged browser identity and agent attempts to bypass Update/Delete authorization.

## Context
- [US-011](../user-stories/US-011-operate-agentboard-through-mcp.md)
- [US-012](../user-stories/US-012-approve-agent-updates-and-deletions-in-the-client.md)
- [security](../technical-architecture/security.md)
- [mcp-tools](../technical-architecture/mcp-tools.md)
- [approval-flow](../technical-architecture/approval-flow.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-001](T-001-establish-backend-and-database.md)
