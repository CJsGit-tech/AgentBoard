# Agent Approval Flow

> Owner: Solution Architect | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Define permission for agent changes to existing records. **Related:** [US-012](../user-stories/US-012-approve-agent-updates-and-deletions-in-the-client.md).

## Rules

| Operation | Permission after local client authorization |
| --- | --- |
| Read or genuinely create a record/association | No per-operation approval |
| Update, complete a ticket, replace a link, restore content | Verified client approval |
| Delete a record or remove an existing link | Verified client approval |
| Explicit human action in the local web UI | No second agent approval prompt |

Creating a document must not overwrite an existing one under a Create label. There is no agent-callable approve tool, `approved=true` shortcut, or arbitrary SQL/shell tool.

## Flow

```text
Request exact change → Save pending request / return ID → Needs approval badge
                                   ↓
                         Client presents change
                    ┌──────────────┼─────────────────┐
                  Accept       Reject/cancel    Unsupported/disconnected
                    ↓              ↓                  ↓
           Recheck revision    No mutation       No mutation;
                    ↓                            request stays queryable
           Commit change + audit
```

1. Show the target, proposed payload or deletion consequences, and base revision in the client interface.
2. Bind the decision to server request ID, authenticated client connection, target, payload hash, base revision, expiry and one use.
3. Accept applies only that change atomically. Do not hold a database transaction open while waiting for the user.
4. Short interactions may finish inline; long interactions return a queryable request ID.
5. Clear **Needs approval** only when the ticket has no remaining pending requests. Its existing task status is unchanged.

## Failure Behavior

| Situation | Required behavior |
| --- | --- |
| Decline, cancel or expiry | No business mutation |
| Client lacks verified approval support | Return `approval_required` + request ID; leave pending for a capable-client retry until expiry |
| Connection disappears | Never infer approval; no unverified change |
| Target revision changes | Invalidate old approval; reject stale commit; obtain a new decision |
| Agent says approval was granted | Reject the assertion as authorization evidence |
| Several requests target one ticket | Resolving one does not clear the others' badge |

## Trust Boundary

Use verified user elicitation where available. Native confirmation requires a separately verified integration conveying the user's decision; a generic tool prompt alone is insufficient. The client is trusted to report that decision: this design cannot protect against a malicious client fabricating it.

[Client compatibility](mcp-tools.md) · [Database constraints](data-model.md) · [Request expiry](activity-logging.md) · [Deletion consequences](api-contracts.md)
