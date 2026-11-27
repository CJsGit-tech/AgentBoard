# Record content and file formats

Use Markdown for readable text in chat and the repository. The AgentBoard reader displays headings, bullet lists, bold text and code. Plain IDs for records in the same project open those records. Set the document type, title, project and short description in native fields. Use the server's revision for edits. Keep unpublished planning Markdown, visual sources, screenshots and runnable contracts in the resolved [local workspace](local-workspace.md). Reuse the confirmed checkout when one exists; a host-side planning folder can be prepared before code or Docker file access is configured. Use a repo-relative path plus a commit or named local snapshot in the record that describes them.

## Document templates

New core documents start with the line `State: Draft`. Add `Open` beside unknown decisions. Keep this state in the document text.

### Product Brief

Use `document_type: product-vision` and one current Product Brief per project. Use three sections.

```markdown
## Product Overview
One paragraph about the product, audience and intended outcome.

## PainPoints
- A specific problem the user faces.

## Features & Value Proposition
**Saved place search**
- Users can find a saved spot when their list grows.
```

### Technical Stack

Cover target platforms, the application stack, data and integrations, local setup, deployment, evidence, and open choices.

### User Experiences

Use `document_type: user-story` and the title `User Experiences` for the project's current document. Use the numbered block below for every user story in a draft or saved document. Continue the numbering across sections. When the document covers existing and planned features, put verified current stories first and planned stories after. Use observable validation checks for the journey and any relevant blocked or recovery states. Mark unresolved product choices **Open**. Keep file links out of the draft and saved content.

```markdown
State: Draft

## Current features

### User Story 1:

- Description
  - As a user, I want to see the latest run status so I know when work needs my attention.
- Validation
  - The run shows its current status and last reported time.
  - If updates stop, the last report remains visible.
```

### Design Profile

Design Profile is the screen-design deliverable. Prepare its written design decisions and build the concrete screens as local drafts using the [Visuals contract](visuals.md). For an explicit chat-only request, prepare the design specification in chat and defer runnable file-based drafts. Review the package locally or in chat/IDE, then save the approved written profile as `design-topic` and upload the approved canvas as its attachment. UserScreens provides the Feel/Flow/Show intent; Design Profile realizes it through concrete layout, widgets, styling, interactions, and states.

- **Design intent and sources** — Identify the journeys and UserScreens blocks being realized, selected screens, devices, and states. Local/chat sources are valid during preparation; preserve their baselines without inventing record IDs.
- **Shared visual decisions** — Record the selected [visual direction](planning.md#choose-a-visual-direction), palette, typography, spacing, component appearance, and accessibility rules once and reuse them across screens.
- **Screen realization** — Specify composition, widget anatomy, button placement, information density, charts, progressive disclosure, and interaction states. Explain how the visible choices satisfy each screen's Feel/Flow/Show intent rather than duplicating the full UserScreens description.
- **Local drafts and rationale** — Link the narrative and runnable screen drafts, identify illustrative data, and explain the principles behind important choices. Use the [local build procedure](visuals.md#build-the-local-draft).
- **Review and publication** — Incorporate feedback in the local version. Record the verified publication reference only after approval and successful upload; use the [publication procedure](visuals.md#publish-and-verify).

### UserScreens

When requested, prepare a separate document titled `UserScreens` with `document_type: design-topic`. Describe how the app should look, feel, and behave through three core dimensions: **Feel (Visual Hierarchy)** sets focal points, contrast, and layout structure; **Flow (User Experience & Progressive Disclosure)** guides tasks and reveals information/actions when needed; **Show (Information & Visual Density)** balances useful detail and scannability without clutter. Use User Experiences and conversation decisions, whether local or saved. Put verified current screens before planned screens and continue numbering across sections. Keep explicit user constraints and observable behavior here; Design Profile supplies the concrete screen designs. Prepare and review this document locally or in chat before saving the approved version.

```markdown
State: Draft

### Screen 1:

- Description
  - Dashboard. Help users see project progress and choose what needs attention.
- Feel (Visual Hierarchy)
  - Make completion and urgent work the first focal points; group supporting details below.
- Flow (User Experience & Progressive Disclosure)
  - Let users open a milestone for its tickets; reveal editing actions when an item is selected.
- Show (Information & Visual Density)
  - Show completion, ticket counts, and blockers first; defer detailed activity until requested.
- Validation
  - The progress display includes a completed ticket count.
  - Users can find blocked work and open its details without scanning the full activity history.
```

### Design export

Only when the user requests a local `DESIGN.md` export, write the Design Profile's visual rules into the confirmed project checkout. A local/chat draft is a valid source; identify its local snapshot, or record the exact revision when using a saved record. Refresh the export when those rules change. Use UserScreens to brief individual mockups. Keep the export local until storage is approved; exporting does not require uploading its source documents. No external design CLI or service is required.

### Screen Inventory

For HTML visuals, attach the canvas to Design Profile with a change note and exact source revisions. Follow the [local review and publication flow](visuals.md). For requested still images, use a `screen-inventory` with screen names, states, devices, sources and PNG paths.

## Ticket payload example

Send this to `create_record` after verifying all fixture IDs in the real project. A BUG with missing reproduction can be saved with the unknowns stated in the description.

```json
{
  "kind": "tickets",
  "fields": {
    "name": "Show an empty state for unmatched place searches",
    "project": "P-123456789abc",
    "milestone": "M-123456789abc",
    "status": "Planned",
    "work_type": "BUILD",
    "execution_role": "FE",
    "tags": ["saved-places"],
    "role": "R-123456789abc",
    "documents": ["D-123456789abc"],
    "description": "Outcome: show a clear empty state.\nAcceptance: an unmatched query shows the message and a clear button."
  }
}
```

Use live milestone, role, and Context document IDs for saved tickets. Use the example tag only when the project catalog contains that active ID and it applies to the ticket. See [managed tags](tags.md).

For a criterion-level handoff, save `criteria` after reading the ticket schema. Each criterion has a stable `id` and observable `text`. Set `evidence_required` when completion depends on proof. Pin `design` with the reviewed publication's `document_id` and `version`. After saving each relevant evidence document as a ticket Output, record verified targets within the matching criterion:

- Report proof uses `kind: report`, `document_id`, the current `revision`, and an optional zero-based `section_line` for the relevant Markdown heading.
- Screenshot proof uses `kind: screenshot`, `document_id`, and the exact `filename` and `digest` returned by readback.

Record `status` per proof. Leave it `unverified` until reviewed and openable. Preserve replaced proof with `superseded` on that criterion when applicable.
