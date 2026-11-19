# Contract: User-Stories <ProjectName>

## Purpose
Convert the Product Vision into user outcomes with testable acceptance criteria; not engineering tickets.

## Preconditions
A usable Product Vision with the product, target users, pain points, and features/value (a blank template is not sufficient). Resolve material scope questions in conversation; do not require additional Vision sections. Use the installed AgentBoard app as the canonical target; local project creation requires user-approved fallback.

## Owner
Product Manager — `agents/product-manager.md` if locally configured; else `roles/product-manager.md`.

## Required context
Read `references/document-folders.md` and `references/artifact-metadata.md` first. For folder-layout projects, inspect the relevant README and open only selected story/topic files; do not assume old combined document paths.

Read the actual Vision, existing stories/IDs, approved decisions, and `assets/templates/user-stories.md` / `assets/templates/user-story.md` from the selected canonical target. Use local paths only in local mode.

## Execution
1. Resolve the canonical target: use the verified AgentBoard project when connected; use local files only for confirmed local mode. Ask before first-time local fallback. Read the current Vision record/file; don't reconstruct requirements from command name.
2. Reference Vision features by name when goal/use-case IDs are absent. Identify MVP user journeys and compose an appropriately sized set of stories (often 6–12) as "As a [user], I want [capability] so that [benefit]."
3. Retain stable `US-###` IDs and titles. Each story contains exactly three fields, in order: `Story`, `Acceptance Criteria`, and `Associated Features`. Use the template's top-level field bullets and nested content bullets. Story contains one description; Acceptance Criteria contains testable bullets covering success, edge, permission, and failure paths where relevant; Associated Features contains exact feature names from the current Product Vision. No priorities, dependencies, notes, open-question fields, story index, or scope/coverage sections. Add the required YAML header; `feature:` tags must exactly match Associated Features. Keep owner, version, status, and date metadata above the story details.
4. Preserve established story IDs and agreed scope. Ask material business-policy questions in conversation rather than inventing answers or adding fields to the document.
5. In connected mode, write each story directly as an AgentBoard document record with metadata fields and verify its returned ID; do not create a parallel local copy. In local fallback mode, write one `docs/user-stories/US-###-short-title.md` file per story and maintain the README. Archive prior files/records on authorized revisions; update a local folder-layout manifest only in local mode. For existing legacy single-file projects, retain their current format until migration is authorized.
6. Validate and update manifest; report exact saved path and next command(s).

## Output artifacts
AgentBoard story/document records when connected; otherwise `docs/user-stories/README.md` plus individual files in approved local mode.

## Acceptance checks
- Follow references/output-consistency.md: synchronize marked navigation, then run check_outputs.py --project <project> --strict. Preserve human text; fix source/schema/example drift before reporting consistency.
- Stories correspond to real product scope, actors, goals and acceptance criteria.
- Stable unique IDs and titles; exactly Story, Acceptance Criteria, and Associated Features per story, with nested bullets and exact Vision feature references. No additional content sections or fields.
- File persisted and project manifest state/version reflect it.

## Persistence updates
Persist story records directly to the verified AgentBoard project, or update the local `stories` artifact and change impacts in local mode.

## Failure handling
If Vision is missing or unusable, recommend `Vision-Document <ProjectName>`; do not invent it. When AgentBoard is missing and local storage is not yet approved, **ask before any local creation**.
