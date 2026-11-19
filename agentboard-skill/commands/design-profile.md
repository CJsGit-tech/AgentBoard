# Contract: Design-Profile <ProjectName>

## Purpose
Author a distinctive product-experience and visual/interaction specification; do not implement UI code in this command.

## Preconditions
Usable Product Vision and User Stories locally or through verified remote reads. AgentBoard is not required.

## Owner
Product Designer (UX/UI) — project `agents/product-designer.md` if present; consult Frontend Programmer for feasibility, not automatic subagent launch.

## Required context
Follow SKILL.md’s Confirmed platform and deployment policy. Read the project’s recorded target clients and deployment constraints before choosing layouts, dependencies or tests.

Read `references/document-folders.md` and `references/artifact-metadata.md` first. For folder-layout projects, inspect the relevant README and open only selected story/topic files; do not assume old combined document paths.

Require the project's `docs/tag-vocabulary.json` before writing tagged Markdown. If absent, derive it from the existing Product Vision and preserve exact feature names.

Persisted Vision, Stories, existing technical constraints/design/branding, `assets/templates/design-profile.md`, optional `assets/templates/design-tokens.json`.

## Execution
1. Use the verified AgentBoard project by default. Use files only for a confirmed file-only project; if AgentBoard is not installed and no target is selected, ask before file creation. If an installed app fails to start or lacks a required operation, report the blocker and stop. Read current Vision, Stories and relevant architecture from the selected target.
2. Define a specific aesthetic direction, UX principles and anti-patterns appropriate to product/users. Avoid generic adjectives without actionable meaning.
3. Cover information architecture/navigation, density, hierarchy, progressive disclosure, component behavior, accessible interactions and responsive patterns.
4. Specify color roles and palette, semantic states, typography, spacing/layout, UI components and interactions (hover, focus, loading, empty, error and success). Include light/dark behavior when applicable. Specify visible inset keyboard focus without external halos, and dropdown icons with reserved internal padding that never cross control borders.
5. Trace key screens/flows to `US-###`; record design assumptions and potential architectural conflicts.
6. Follow `references/concise-design-documents.md`. Write a short `docs/designs/README.md` task index and focused topic files using `assets/templates/design-topic.md`. Add the required YAML header to every canonical Markdown file and use only relevant feature tags, plus optional cross-cutting concerns where useful. Keep core topics and add feature topics from real stories. Map screens to stories within their relevant topic; do not create a combined Design Profile.
7. In connected mode, write design topics and optional tokens directly to AgentBoard, preserving metadata and verifying record IDs. In local fallback mode, archive replaced files and maintain the folder manifest. Do not use the single-file writer on a folder artifact.
8. Define the complete screen inventory for Create-Screens; do not generate screens here. Run the applicable consistency checks. Report AgentBoard IDs or local paths and unresolved decisions.

## Output artifacts
- AgentBoard design/document records when connected; or local README, concise topic files and optional tokens in fallback mode

## Acceptance checks
- Actionable design direction and consistent navigation, density, hierarchy, interaction, progressive disclosure and accessibility.
- Screen inventory mapped to real stories; tokens parse as JSON if delivered.
- Saved files and manifest statuses agree; no production UI code generated.

## Persistence updates
Write directly to AgentBoard when connected; update the local `design` and optional `tokens` manifest entries only in local mode.

## Failure handling
Record nonblocking assumptions or ask one essential brand/platform question when genuinely required. AgentBoard connectivity is not needed for an **approved** local draft; first-time local storage requires explicit consent.
