# Contract: Vision-Document <ProjectName>

## Purpose
Author and save a concise, human-readable Product Vision (~1–2 pages unless otherwise requested).

## Preconditions
- Named or unambiguously established project, with verified AgentBoard storage or **approved local project**. If missing, ask for local confirmation before creating it.
- Enough user-provided concept context to write a meaningful document; don't fabricate the product's premise.

## Owner
Product Manager — use project `agents/product-manager.md` if present; otherwise `roles/product-manager.md`.

## Required context
Project information and constraints, existing Vision or decisions, `assets/templates/product-vision.md`, `references/artifact-metadata.md`, quality gates.

## Execution
1. Resolve existing, authorized project storage. If no approved local project exists and AgentBoard cannot be used, **stop to ask the storage-choice question**, with no writes; after approval, scaffold and read existing docs/manifest and customized role definition.
2. Identify the product, target users, pain points, and features with their user value. Ask one essential question only if meaningful work cannot proceed; otherwise label assumptions inline.
3. Use exactly three content sections: `Product Overview` (one paragraph), `PainPoints` (bullet points), and `Features & Value Proposition` (each feature on its own bold line followed by one or more value bullets). Use no feature/value table or additional content sections. Add the required YAML header; derive `feature:` tag IDs from exact feature names and the project vocabulary, keeping concern tags only when useful. Keep owner, version, status, and date metadata in the body. Do not require goals or use-case IDs in this concise format; preserve existing IDs in revision history and use feature names for downstream references.
4. Generate a **complete project-specific Markdown document**, with owner, version, draft status and real date. Add `docs/tag-vocabulary.json` from the template: derive stable feature IDs from exact Vision feature labels and keep the optional concern list small and defined. Do not merely copy a blank template.
5. If AgentBoard is connected, create or update the tag vocabulary before writing a Vision record that uses its tags, and persist both directly through verified app operations, keeping frontmatter values in structured metadata and verifying returned record IDs. For an existing approved record, follow its update-approval flow; do not silently overwrite it. If the user selected local fallback, save `docs/product-vision.md` and `docs/tag-vocabulary.json` with `scripts/save_artifact.py`, and link the guide/catalog from `docs/README.md`.
6. Validate the selected target, report the actual AgentBoard record IDs or local paths, version and unresolved assumptions. Mention affected downstream artifacts on revision. Never claim a remote write without a verified tool result.

## Output artifacts
One Product Vision and a controlled tag vocabulary in the selected canonical target: AgentBoard by default when connected, otherwise explicitly approved local files.

## Acceptance checks
- Exactly the three specified sections; overview is one paragraph, pain points are bullets, and each feature is followed by value bullets.
- Product, users, and value are clear; unknowns are labeled inline. No additional sections or tables.
- User can understand it without engineering documents; file is actually saved and manifest updated.

## Persistence updates
AgentBoard record metadata is updated through verified operations when connected; local manifest entries are updated only in local fallback mode.

## Failure handling
If product concept is genuinely unknown, ask one critical question rather than invent it. Missing AgentBoard is not a failure, but requires **an explicit Yes before first-time local writes**. A No cancels fallback.
