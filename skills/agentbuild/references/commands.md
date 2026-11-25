# AgentBuild command guide

Start with the skill name and one of these four commands. In Codex, write `$agentbuild Create Tickets` and describe the work in the same message. In Claude Code, use `/agentbuild Create Tickets`. Give details in ordinary sentences. Document impact reviews and ticket scope checks run inside these workflows. Scope changes need the user's decision; documents and designs are prepared locally or in chat before the reviewed version is approved for storage. See [Change reviews](reviews.md).

## Setup

- Find the project or create it by name, initialize missing roles, and check the core documents. The Setup command authorizes these steps.
- **Input** — Project name or existing ID. Include the checkout path if needed.
- **Output** — Links to the project and its roles, the status of the four core documents, and prepared local planning/visual/evidence folders. See [Local workspace](local-workspace.md). [Setup contract](planning.md#project-structure)

Example: “AgentBuild Setup PocketMap.”

## Create Documents

- Check which core documents exist, then prepare the selected documents one at a time using their own [question subsets](planning.md#document-questions) and follow-ups from the conversation. Use User Experiences for product behavior, UserScreens for Feel/Flow/Show, and Design Profile for concrete screen designs and local visual drafts. Use Tag Catalog to maintain project tags.
- **Input** — Project name or ID. Name documents to limit the scope or give changes for an existing document. “All” selects the four core documents. Request UserScreens for a separate screen-experience document. Local drafts and chat previews are the default; “chat only” avoids local files. For Tag Catalog, give the tags or assignments to change.
- **Output** — Document status, reviewable local/chat drafts, local screen drafts when Design Profile is selected, and links and revisions after approved content is saved. [Document contract](planning.md#planning-documents) · [Tag Catalog](tags.md)

Example: “AgentBuild Create Documents for PocketMap.”

## Create Visuals

- Prepare the Design Profile's concrete screen designs: present the narrative, build React/Mantine drafts, and deliver a local interactive HTML canvas. Review and revise locally before uploading the approved version.
- **Input** — Project and optional flow, screens, states, or ticket to link. Use User Experiences for behavior, UserScreens for Feel/Flow/Show, and Design Profile for design choices. Sources may be local/chat drafts or saved records. For a project canvas, put current screens first and planned screens after.
- **Local output** — A version folder in the [local workspace](local-workspace.md), containing `design-narrative.md`, a built `gallery.html` with readable narrative notes and Mantine screen drafts, their bundled local assets, `canvas-files.json`, and source baselines. Prepare `publication.json` with exact saved source revisions when the approved package is ready for upload.
- **Published output** — A numbered canvas publication attached to Design Profile. Follow the [single publication and verification procedure](visuals.md#publish-and-verify).

Example: “AgentBuild Create Visuals for PocketMap. Show the saved-places screens and an empty saved list.”

Follow-up after review: “Upload this version and link it to the empty-state ticket.”

## Create Tickets

- File work or bugs in a project milestone.
- **Input** — Project, milestone, type (FE, BE, FE-Bug, BE-Bug, or Bug), and the requirements or report. Context IDs and managed tags are optional. Say if a missing milestone should be created.
- **Output** — Planned AgentBoard tickets with the work type, execution route, acceptance criteria or bug details, and applicable Context links and tags. A request for a ticket-plan draft instead produces local `ticket-plan.md` and its chat preview without filing records. [Ticket contract](tickets.md) · [Local workspace](local-workspace.md)

Example: “AgentBuild Create Tickets for PocketMap, First Release. FE-Bug: tapping Save leaves the form open and shows no confirmation.”
