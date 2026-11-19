# Plain document folders

## Organization

Use ordinary editable Markdown files and relative links. No snapshots, section database, generated exports or custom context store.

```text
docs/
  product-vision.md
  README.md
  user-stories/
    README.md
    US-001-create-project.md
    US-002-switch-projects.md
  technical-architecture/
    README.md
    system-architecture.svg
    constraints.md
    technology-stack.md
    data-model.md
    api-contracts.md
    mcp-tools.md
    approval-flow.md
    document-history.md
    activity-logging.md
    source-layout.md
    security.md
    deployment-operations.md
    decisions.md
    risks-and-references.md
```

The tree above illustrates existing projects. For new Technical-Documents output, use the fixed shared + web/iOS profiles and optional-topic decisions in `architecture-document-profiles.md`. Run the skeleton script only after plan confirmation; unfinished skeletons are not complete drafts. Existing folders stay supported until an authorized revision.

Every canonical Markdown file in these folders starts with the compact header in `artifact-metadata.md`. Keep tags specific to the file's real feature coverage; cross-cutting concern tags are optional. Exclude archived history, review reports and screen evidence from the active metadata catalog.

## Read selectively

Humans and agents start with the appropriate README listing titles and relative links. Story navigation includes the associated Product Vision features. Open only relevant story IDs and technical topic files. Follow their related-topic links when the current task needs those rules. The architecture README contains a short system overview, module diagram link, and topic navigation; detailed requirements belong in their topic files, not repeated in the overview.

For example: document restore → US-015 → document-history.md → approval-flow.md if an agent changes content → mcp-tools.md if implementing its interface.

## Stories

One file per stable US-### ID; filename `US-###-short-title.md`. Retain the established `### US-### — Title` heading and YAML metadata before it. Feature tags must exactly match the story's Associated Features; add concern tags only when useful across-feature retrieval is intended. Each story contains only Story (one description bullet), Acceptance Criteria (bullets), and Associated Features (exact Vision names as bullets). A README is navigation, not another copy of story content. Cross-feature stories have one canonical file and may have multiple feature associations.

## Technical documents

One coherent topic per file, with descriptive headings, YAML retrieval metadata, owner, version, status and real date. Keep the SVG inside technical-architecture/. Preserve ADR IDs in decisions.md. Link policy owners from APIs/data docs instead of repeating the same approval/history/retention rules. The required architecture topics must be covered across the folder, not all repeated in every file. Still perform the multi-round discovery and confirm the brief before drafting or changing architectural decisions.

## Updates and additions

Edit the actual Markdown file. For an explicit revision, preserve its prior version under `history/<story-id-or-topic>/<version>.md` before replacing it. Advance its version/date and update navigation if a title, filename, feature association or description changes. Keep IDs stable. When adding a story, choose an unused ID, create one file with matching metadata and add its README row. When adding technical detail, prefer the existing appropriate topic; otherwise create a topic file with focused tags and add its README link. Inspect related stories/specifications for semantic impact; do not silently rewrite approved decisions. These remain author responsibilities, not a claimed atomic multi-file transaction.

Manifest collection entries use `layout: folder` and point to the relevant README; the SVG entry points to its actual file. The README carries the artifact collection's owner/version/status/date. Preserve individual files' own revision metadata. Update manifest collection versions deliberately when the collection changes. Local project consent rules still apply.

The legacy save_artifact helper handles single-file artifacts only. It rejects folder entries so an entire story document cannot accidentally overwrite README.md. Folder files are authored using ordinary filesystem edits, with manual history preservation and manifest updates. Run `validate_project.py` afterwards; it checks story IDs, one story per file, filename IDs, the three-field format, Vision features, README coverage, local file links, symlinks, SVG XML and required architecture coverage. It does not prove semantic correctness, fetch external links, or validate remote URL targets.

Existing single-file projects remain supported until the user requests migration. Read artifact paths in the manifest rather than assuming either layout. During migration, back up both original documents, SVG and manifest, then split content without changing requirements. Remove old active combined files once originals are safely archived and the new layout validates.

## Contracts and JSON examples

Apply `contracts-and-examples.md`. Keep exact OpenAPI/domain/MCP schemas under technical-architecture/contracts/ and labeled examples under examples/. Skeleton contract scopes must be resolved and examples validated before reporting completion. Existing topic names remain supported; no automatic reorganization is required.

## Completion consistency

Follow output-consistency.md. Use sync_navigation.py for explicitly marked story/MCP navigation blocks and check_outputs.py --strict for one read-only gate. Derive indexes from canonical sources, declare important example outcomes/statuses, and keep semantic review separate.

Design output: follow [concise design documents](concise-design-documents.md) for a short task index and focused topics.
