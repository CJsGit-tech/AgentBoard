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
