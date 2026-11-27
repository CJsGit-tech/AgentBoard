# Agent document and scope checks

These are agent checks, not a user review workspace. Do not add a Reviews page, review queue, or separate approval dashboard. Keep preparation notes with local drafts or in chat. Formal requests, checked document revisions, findings, scope decisions, and execution holds use the existing Runs & activity log once record writes are authorized. Ask scope questions in the current chat.

Run these checks inside the active named workflow. They do not require the user to invoke another command. They do not authorize unrelated features or automatic publication. Setup remains read-only for documents and needs no scope confirmation.

## What must be checked

For a new feature, screen change, requirements edit, or new/changed ticket, read the current requirements and request before preparing the draft. Compare proposed changes locally or in chat and retain the sources, findings, and user decisions there. Draft preparation does not require a saved target, a placeholder record, or a formal review write. For an existing target, use `start_change_review` with its current revision before an authorized storage edit when the originating request is not already recorded. For a new target, create the record only when its storage write is authorized, then read and assess its current review, starting one if needed. Normal Create Tickets authorization to file Planned tickets is unchanged. AgentBoard creates reviews when relevant content or relationships change. Preserve scope confirmation already given and its conversation reference; do not ask the same question again.

Use `list_change_reviews` with the project and optional subject and page all results. Read the current, non-superseded review's `snapshot`, including the saved content, exact revisions, and last reviewed scope baseline. Reuse existing same-project Context/Output links and managed tags. Documents have a `source_documents` list for the documents they depend on. Follow source links and related tags. If links/tags are incomplete, inspect the project core documents and related work before declaring coverage complete. Tags discover candidates; they do not prove agreement.

A saved draft or an agent's previous assertion is not evidence that the user approved a new feature. Cite the relevant document section or recorded user decision in each finding. Missing agreement or ambiguous requirements should be recorded as `Unclear`; ask one focused clarification only when needed. Do not invent approval or mark every record as checked without reading it.

## Submit the findings

Use `assess_change_review(id, revision, assessment)` with:

```json
{
  "conclusion": "Within scope",
  "rationale": "The saved Save story already requires this validation. This request changes no agreed behavior.",
  "findings": [
    {
      "document_id": "<document-from-the-snapshot>",
      "outcome": "No update needed",
      "reason": "User Story 3 requires an error beside an invalid field. The existing story covers this fix."
    }
  ]
}
```

Give exactly one finding for every snapshot document. Use `No update needed` or `Update required`, with evidence and a reason. The overall conclusion is `Within scope`, `Scope change`, or `Unclear`. Explain the precise added, removed, or changed behavior for `Scope change`; also identify required document edits. These are semantic judgments supplied by the agent or person, not an automatic AI result from the app.

| Result | Next step |
| --- | --- |
| Ready | Continue authorized work without another confirmation. |
| Needs updates | Prepare affected document updates locally, save the reviewed version when approved, then read and assess the new current reviews. Reuse approval already given for that version. |
| Unclear | Collect the missing product decision or evidence. Continue independent work where possible. |
| Awaiting confirmation | Explain the exact scope difference in chat. Wait for the user's decision, then record their exact words and conversation reference. |
| Confirmed | Continue the confirmed scope after required document updates and other impact checks are complete. |
| Declined | Keep the existing agreed scope. Revise the proposal or leave the work stopped. |
| Superseded | Read the replacement current review. Earlier findings and confirmations are historical. |

Scope confirmation belongs to the user. Agents must never decide for them or infer consent from silence. Ask for scope confirmation only when the agreed scope changes; approval to store a reviewed document/design follows its local review flow. After an explicit scope decision about the exact proposal, call `record_user_scope_decision(id, revision, accept, user_quote, conversation_reference)` once the formal review exists. Use the user's exact words and a traceable chat reference. This records the user decision via the agent's identity in Runs & activity; it does not impersonate a direct Human action. The server still rejects stale decisions and keeps required document updates unresolved. Do not use the browser HTTP endpoint or invent a second confirmation when the exact scope was already agreed. A later, different proposal needs a new decision.

Document edits save in place with history and a pending impact review. Their last reviewed baseline stays intact until the new check is resolved. Record a scope difference for proposed content that changes the agreement; do not treat the saved draft as approved. If the scope change was declined, restore or revise the pending content to match the retained agreement as authorized. Deleting a requirements document uses a `Delete` impact review and user scope confirmation before removal. Existing link protections still apply.

## Before implementation or publication

The server requires a current Ready/Confirmed ticket scope check and current document impact checks for the ticket's requirements before moving it to In progress or Done, or starting/completing an editing run. Supply a linked ticket for `mode: Edit`; `mode: Read only` permits inspection and questions without changing project files. Never label editing as read-only to bypass checks. Output documents describe produced evidence; they do not replace Context requirements. Before marking a ticket Done or an implementation run Completed, also perform the [evidence completion gate](tickets.md#evidence-completion-gate). Scope checks alone do not verify the evidence handoff.

Read the current checks before editing, after scope/source changes, and when resuming a session. Requirement changes mark affected editing runs Waiting for input. AgentBoard records this hold but cannot stop an external Codex/Claude process; the agent must pause edits itself. Resume only after the checks clear. Unrelated work and read-only inspection can continue.

New HTML canvas publications and PNG uploads also require current document impact reviews. Preserve the existing local review and explicit-upload boundaries. A frozen publication and a metadata-only attachment upload do not change the requirements baseline. Confirm content freshness, not just record revision counters.

Record and review mutations use current revisions. On conflicts or uncertain responses, reread before retrying; never blindly replace revision numbers. The server preserves input snapshots and superseded checks, and records assessments and scope decisions in History and Runs & activity. Report document names, findings, and the existing Runs & activity link at `/#activity` on the verified origin. Do not send the user to a separate Reviews page. Keep raw IDs in tool payloads.
