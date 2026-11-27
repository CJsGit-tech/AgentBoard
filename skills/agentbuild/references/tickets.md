# Create Tickets

For a requested local ticket-plan draft, use the [local workspace](local-workspace.md), preserve source baselines, and show the plan without filing records. Otherwise, Create Tickets retains its normal authorization to file Planned tickets.

Resolve the project and a live milestone from the request or verified context. Ask if several milestones fit. If the named milestone is missing, create it only when the user requests that as part of Create Tickets. Verify the new milestone ID before filing tickets.

| Type | `work_type` | `execution_role` |
| --- | --- | --- |
| FE | BUILD | FE |
| BE | BUILD | BE |
| FE-Bug | BUG | FE |
| BE-Bug | BUG | BE |
| Bug | BUG | Empty if the execution area is open |

For BUILD, describe the outcome and testable acceptance criteria. For BUG, preserve observed behavior, known reproduction steps and expected behavior. Mark unknowns clearly. Use a live project role ID when ownership is known. Link relevant same-project documents as Context. A visual inventory can provide the paths to source mockups.

Perform the [required scope and document impact checks](reviews.md). Creating a Planned ticket records a proposal; it does not approve new scope. Read the current review snapshot, compare the requirements with linked documents and recorded agreement, and submit evidence for every document. Explain any extension or contradiction and explain the difference in chat and collect the user's explicit scope decision. Log that decision with its exact quote and conversation reference. Within-scope work needs no extra approval. Missing context and unclear agreement must be resolved before implementation. The backend gates In progress, Done, and editing runs. Preserve Output links for documents produced by the work.

Use the [Tag Catalog](tags.md) to find relevant project records and apply valid tags. Search existing tickets for duplicates before saving. If a matching ticket exists, link to it. Create the requested new tickets as Planned, read them back, and report their routes with links to the tickets. See [the ticket payload example](formats.md#ticket-payload-example) for the MCP format.


## Evidence completion gate

Apply this procedure when executing authorized tickets, including implementation requested after Create Tickets. This is an agent completion requirement; do not assume the backend checks whether evidence has been uploaded.

1. **Prepare factual evidence.** Record what changed, the exact checks performed and their results, relevant screenshots, known failures and unverified acceptance criteria. Identify the build or revision and environment tested. Distinguish native implementation screenshots from design mockups. A completed test run is not a clean accessibility result when its audit still reports findings. Do not run unrelated checks or invent screenshots to fill the report.
2. **Save evidence in AgentBoard.** Use a `review-evidence` document for the verification report and relevant test-log excerpts. Use a `screen-inventory` document and `attach_visual` for supported screenshot attachments. Reuse the intended evidence records where appropriate. Keep large or unsupported raw artifacts locally and state which remain local; upload the readable results needed to assess the ticket. Do not include secrets or unrelated user data.
3. **Link every affected ticket.** Add the evidence records to `output_documents` using current ticket revisions, preserving existing Output links. Shared evidence may serve several tickets when the report clearly maps results and limitations to each. Keep approved requirements in Context; evidence belongs in Outputs.
4. **Verify the handoff.** Read saved evidence and tickets back by ID. Check report content, screenshot filenames and digests against the local artifacts, and each affected ticket's Output links. Open a ticket's Links → Outputs and confirm the report and screenshot previews are accessible in AgentBoard. A local path or a successful upload response alone is insufficient. Complete any required document impact and ticket scope checks using [Change reviews](reviews.md).
5. **Close only verified work.** Mark a ticket Done only after its acceptance criteria are satisfied and its evidence handoff is verified. Mark its implementation run Completed only after its produced evidence is saved, linked and verified. Report remaining acceptance work accurately; evidence upload does not make incomplete implementation complete. Include the verified ticket and evidence links in the final response.

Saving factual implementation and verification evidence is included in the user's authorization to execute the ticket. It needs neither another Create Documents command nor a separate design approval. This does not authorize new requirements, changed designs, broader sharing or unrelated publication. Proposed requirements and design packages still follow their existing draft approval boundaries.

If upload, linking or readback fails, preserve the local evidence and successful partial writes, leave the affected ticket/run uncompleted, record the failure in its activity note and explain the incomplete handoff with clickable local paths. Read current records before retrying and reuse successful writes to avoid duplicates. If the user explicitly requested local-only or chat-only delivery, honor that instruction and clearly report that the AgentBoard evidence handoff was intentionally deferred.
