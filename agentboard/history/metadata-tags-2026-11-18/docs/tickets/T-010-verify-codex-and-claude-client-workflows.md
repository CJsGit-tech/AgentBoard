# T-010 — Verify Codex and Claude MCP client workflows

Role: BE
Type: BUILD
Status: Open
Verification: Not applicable
Assignment: Confirmed
Depends on: T-009
Estimate (days): 3
Estimate scope: Build
Estimate basis: Provisional/high uncertainty: four-client validation/configuration and a minimal bridge if required; unavailable clients or mediation may require re-estimation.

## Outcome
Actual client configuration support is evidenced, with unsupported approval handled without weakening permissions.

## Acceptance Criteria
- Save setup instructions, versions/capabilities and actual discovery/Create/Read/revision/activity outcomes for Codex desktop, Codex CLI, Claude Code and Claude Desktop.
- Exercise supported approval accept/decline/stale paths and unsupported approval behavior; an absent client is reported untested/blocked, never passed.
- Verify restart/reconnect and duplicate calls. Add a thin stdio bridge only where actual client transport needs it, preserving identity, approval and cancellation.
- Publish a truthful compatibility matrix and reproducible evidence; never infer that all clients work merely because MCP discovery works.

## Context
- [US-011](../user-stories/US-011-operate-agentboard-through-mcp.md)
- [US-012](../user-stories/US-012-approve-agent-updates-and-deletions-in-the-client.md)
- [US-015](../user-stories/US-015-read-compare-and-restore-document-revisions.md)
- [mcp-tools](../technical-architecture/mcp-tools.md)
- [approval-flow](../technical-architecture/approval-flow.md)
- [risks-and-references](../technical-architecture/risks-and-references.md)
- [Assigned role](../../agents/backend-programmer.md)

## Dependencies
- [T-009](T-009-expose-typed-mcp-tools.md)
