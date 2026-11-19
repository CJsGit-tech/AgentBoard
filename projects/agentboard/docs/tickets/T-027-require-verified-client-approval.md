---
name: "T-027 — Require verified client approval"
description: "Prevents an unattended MCP client or an unanswered form from applying agent updates and deletions."
kind: "ticket"
tags: ["feature:product-project-management", "feature:task-coordination", "concern:authorization", "concern:security"]
---

# T-027 — Require verified client approval

Role: BE
Type: BUG
Status: Done
Verification: Fixed
Assignment: Confirmed
Depends on: None
Estimate (days): 1
Estimate scope: Repair
Estimate basis: Trace the live client behavior, enforce the approval boundary, and verify both MCP approval transports.

## Outcome

Only an explicit decision from a credential dedicated to a verified interactive client can authorize an agent update or deletion.

## User Report

Discovered during release verification. Claude Code 2.1.327 in unattended `--print --permission-mode dontAsk` mode called `update_project` against a synthetic project. The response reported `applied: true`. A subsequent read returned the new purpose and revision 2. The test provided no human response and contacted only the local mock model and AgentBoard.

## Investigation

The server trusted approval capabilities without verifying the credential's client setup. It also treated a first-round form request as approval when the SDK returned `InputRequiredResult`. The unattended test did not capture the MCP wire branch used for that request.

## Acceptance Criteria

- A default or unverified client can create and read records. Updates and deletions return a pending request without changing state.
- The multi-step form returns signed state and leaves the target unchanged until an explicit matching answer arrives. Missing or mismatched state leaves the target unchanged.
- A verified client's accept applies once. Decline, cancellation or a stale revision preserve the current record.
- Retest the original installed Claude Code workflow with synthetic records.

## Context

- [Approval architecture](../technical-architecture/approval-flow.md)
- [T-008 — Enforce verified client approval](T-008-enforce-client-approved-mutations.md)
- [T-010 — Verify installed clients](T-010-verify-codex-and-claude-client-workflows.md)
- [MCP operation handler](../../backend/app/mcp/operations.py)

## Completion Evidence

The original Claude Code workflow now returns `approval_required`, `applied: false` and a request ID. The follow-up read confirmed the project stayed at revision 1 with its original values. See the [review report](../review-report.md).

In a disposable API instance, real HTTP requests exercised default Delete, the first approval form, missing or altered continuation state, accept and replay, decline, cancellation, stale revision, and two concurrent accepts. The legacy MCP SDK callback also applied one explicitly accepted change. These checks used a synthetic interactive credential. See the [wire run](../evidence/client-approval/wire-results.txt) and [regression tests](../../backend/tests/test_mcp_approval.py).
