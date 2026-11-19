---
name: "Approval states"
description: "Expose protected changes without confusing approval with task status."
kind: "design-topic"
tags: ["feature:task-coordination", "feature:progress-tracking", "feature:document-management", "feature:agent-role-management", "concern:authorization", "concern:auditability", "concern:data-integrity", "concern:security"]
---

# Approval states

> Owner: Product Designer | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Expose protected changes without confusing approval with task status.

**Related stories:** US-008, US-012

**Required context:** [Interaction states](interaction-states.md) and [accessibility](accessibility.md).

- Create/Read are unrestricted for connected agents. Update/Delete requires approval through the Codex/Claude client interface.
- Show Needs approval as a separate ticket badge, preserving its task status. Support multiple pending requests without overwriting their identity.
- Inspector shows proposed differences, request state, copyable request ID and instructions to continue in the client. Do not add an in-app approval button.
- If the client cannot obtain approval, reject the mutation; the board still shows the pending approval badge as appropriate to the request state.
- Explain rejected, stale and expired requests. Never imply approval applied a mutation until canonical acknowledgement arrives.
- Agent restores follow the same Update approval rule. Human restore/delete remains explicit user action without a second client gate.

Follow the existing [approval architecture](../technical-architecture/approval-flow.md) and [contracts](../technical-architecture/contracts/README.md); design must not invent a new authorization mechanism.
