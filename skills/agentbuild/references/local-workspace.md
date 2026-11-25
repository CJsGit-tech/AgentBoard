# Local planning workspace

Use one resolved local project root for planning drafts, visual previews, and evidence. PostgreSQL holds saved AgentBoard records and published Canvas bundles. This host-side workspace holds unpublished work and reproducible source files.

## Resolve and prepare the folder

1. Reuse the project's verified `checkout_path`, an existing local workspace mapping, or the project folder supplied by the user. Use the current directory only when it is confirmed as the tracked project's folder. A planning-only folder is valid before a code repository exists; do not replace an existing code checkout mapping with it.
2. Inspect existing planning and visual directories before choosing paths. Reuse established locations. If the root is unknown or several folders could belong to the project, ask one focused folder question. The AgentBoard service checkout is not automatically the tracked project's checkout.
3. During Setup, create missing directories and a small `workspace.json` location map. Later named workflows may initialize these under their existing authorization. Preserve existing files and mappings. Do not create empty document templates, initialize Git, install packages, start servers, or configure Docker mounts as part of creating folders.
4. Report the resolved root and clickable absolute paths to actual folders and files. If host access is unavailable, report that limit; do not claim the folders were created. Known local planning can continue while the live connection is being repaired, but report canonical saves as blocked until the native tools work.

Use this layout when the project has no established convention. Create document files and individual Canvas version folders only when the selected workflow needs them.

```text
<project-root>/
  docs/
    planning/
      workspace.json
      drafts/
        product-brief.md
        technical-stack.md
        user-experiences.md
        design-profile.md
        user-screens.md
        DESIGN.md
        ticket-plan.md
    designs/
      visuals/
        <flow>/
          version-N/
            design-narrative.md
            gallery.html
            canvas-files.json
            publication.json
            assets/
    evidence/
```

For a project-wide Canvas already stored at `docs/designs/visuals/version-2/`, retain that structure. Do not relocate it or create a competing nested copy just to match the example.

## Location map and draft baselines

Keep paths relative to the resolved project root in `docs/planning/workspace.json`, or reuse the project's existing equivalent. A minimal map is:

```json
{
  "project_name": "Example",
  "paths": {
    "drafts": "docs/planning/drafts",
    "visuals": "docs/designs/visuals",
    "evidence": "docs/evidence"
  },
  "draft_baselines": {}
}
```

For each document draft, record its target record and baseline revision, or that the target is missing, plus the exact source record revisions in `draft_baselines` or existing draft metadata. For unpublished sources, retain local paths and content digests, or the exact chat/IDE draft and conversation reference for chat-only work. Do not invent record IDs or create placeholders to obtain them. Keep IDs in metadata; use names and file links in user-facing output. Recheck the live target and sources before saving. Local file modification times do not prove a saved record is current. Do not copy API keys or `.env` content into planning files.

## Use the workspace

- **Setup:** Prepare locations and report them. Check saved documents without creating placeholder drafts or canonical document records.
- **Create Documents:** Prepare only selected drafts as local Markdown and chat previews, or entirely in chat/IDE when requested. Design Profile also includes local screen drafts using the Visuals contract. Review and revise before any document storage write. Save the approved version, reuse explicit approval already given for it, update the intended record in place, and record the readback revision locally.
- **Create Visuals:** Use current saved sources and identified local/chat drafts to write the narrative, editable preview source, and built gallery under the chosen flow/version folder. Keep source baselines, reviewed runtime files, and manifest together. Prepare publication metadata with exact saved revisions after the approved source documents have been saved. Unpublished revisions may reuse their active draft folder. Preserve a published version's local snapshot; choose an unused folder for the next version and verify the build actually writes there. Never run an old build command that overwrites a published folder. Upload only the reviewed package the user approves; do not ask again for approval already given for that version.
- **Create Tickets:** Put a requested planning draft in `ticket-plan.md`. Default ticket creation still files Planned records under the existing command authorization; local staging does not add another approval step. Keep requirements and source baselines with the local plan.

Creating these folders does not grant the in-app Assistant access to host files. Docker mounts and runtime editing permissions are separate from host-side planning.
