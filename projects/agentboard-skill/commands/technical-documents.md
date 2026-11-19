# Contract: Technical-Documents <ProjectName>

## Purpose
Author implementation-ready architecture guidance and a meaningful, valid SVG system diagram. Keep this documentation separate from coding.

## Preconditions
Usable Product Vision and User Stories in the canonical AgentBoard project, or in an explicitly selected local-only project. Drafts may be provisional.

## Owner
Solution Architect — project `agents/solution-architect.md` if present, otherwise bundled charter; consult Backend/Frontend roles when materially necessary.

## Required context
Follow SKILL.md’s Confirmed platform and deployment policy. Read the project’s recorded target clients and deployment constraints before choosing layouts, dependencies or tests.

Read `references/contracts-and-examples.md`, `references/architecture-document-profiles.md`, `references/document-folders.md` and `references/artifact-metadata.md` first. For folder-layout projects, inspect the relevant README and open only selected story/topic files; do not assume old combined document paths.

Require the project's `docs/tag-vocabulary.json` before writing tagged Markdown. If absent, derive it from the existing Product Vision using the Vision contract; do not invent new product feature labels.

Read local/verified Vision, Stories, existing Design Profile/architecture, repository rules and known platform/SDK/deployment constraints. Templates: `technical-architecture.md`, `system-architecture.svg`. Required policies: `references/architecture-discovery.md` and visual reference `assets/references/system-architecture-modules.svg`.

## Execution
1. Resolve the canonical target: use the verified AgentBoard project by default; if the user chooses file-only mode, ask for consent before scaffolding. If AgentBoard is not installed and no target is selected, ask app vs file-only. If an installed app fails or lacks a required operation, report the blocker and stop. Read the existing Vision, story index/records and relevant technical topics/decisions from that target.
2. Conduct multiple rounds of discovery using `references/architecture-discovery.md`. Ask batches of related questions, wait for replies, and follow up. Cover deployment/access, targeted stack, online providers, execution/integration scope, data, security, scale, and operations. When preferences are absent, propose viable stack/provider options with pros and cons and obtain a choice or delegated decision. Present a concrete readiness brief for confirmation before authoring; a simple app description or deployment answer is insufficient.
3. Select web, iOS or both profiles using `assets/architecture-documents.json`. Classify every optional trigger as its own file, an explicitly named inline section, or not applicable with rationale and requirement references. Confirm this document plan with the discovery brief before running `scripts/architecture_documents.py scaffold`; do not treat a skeleton as authored content.
4. Fill the selected document contracts with module boundaries, data flows, interfaces, persistence, security, operations and platform-specific behavior. Map every actual story acceptance criterion to the selected design documents in document-plan.json.
5. Choose FE/BE technology/SDK/library options with concise rationale, compatibility confidence and meaningful alternatives. Include the selected platform folder plans: web frontend/backend or iOS app structure; shared backend plans only where applicable, with explicit N/A reasons otherwise.
6. Author applicable OpenAPI/domain/MCP schemas under contracts/ and bound JSON examples under examples/. Resolve the scaffold contract manifest; use realistic IDs, explicit record vs interface labels, and representative approval/error outcomes. Validate schema/example conformance with the documented environment. Write relevant `ADR-###` decisions linked to `US-###`, respecting existing design constraints.
7. Generate **real** `system-architecture.svg` from the proposed system, not the illustrative template; follow the supplied module-oriented visual reference: aligned functional modules within frontend/backend groups, deployment boundaries, persistence below, and labeled orthogonal flows. Adapt topology to confirmed requirements rather than copying example technologies.  Verify SVG XML and inspect rendering when possible.
8. In connected mode, persist topic documents, contract records and the diagram directly to AgentBoard using verified operations; store artifact metadata as structured fields and verify each returned record ID. Do not create a duplicate local project copy. In local fallback mode, write ordinary topic files and SVG under `docs/technical-architecture/`, preserve revision history and update folder-layout manifest entries.
9. Validate the selected target and semantic consistency; register local versions/paths only in local mode. Never claim remote persistence without verified results.

## Output artifacts
- AgentBoard architecture/document/contract records and diagram when connected; or local README, confirmed plan, topic files, and SVG in fallback mode

## Acceptance checks
- Follow references/output-consistency.md: synchronize marked navigation, then run check_outputs.py --project <project> --strict. Preserve human text; fix source/schema/example drift before reporting consistency.
- Multi-round discovery completed; readiness brief confirmed or explicitly delegated before authoring. Deployment, stack, providers, integrations, data, and operational choices recorded.
- Confirmed core/platform/optional document plan; skeleton script preserves prior content, and all placeholders have been replaced by real content.
- Constraints and assumptions explicit; technology decisions justified with options and tradeoffs.
- Selected web/iOS source structures are consistent with designed components; iOS-only projects are not forced into web frontend/backend documents.
- SVG is readable, parses correctly and matches the written architecture.
- Every story acceptance criterion has a valid design reference, reviewed for actual behavioral coverage.
- Cross-document consistency, diagram agreement and evidence review recorded; critical/blocking findings resolved.
- validate_contracts.py, architecture_documents.py validate and validate_project.py pass using the contract validation environment when applicable. Files remain drafts, not approved artifacts.

## Persistence updates
Write directly to AgentBoard when connected; in local mode save `architecture` and `architecture-svg` in the manifest with versions and revision history.

## Failure handling
If actual architecture cannot be responsibly designed due to missing material requirements, identify them precisely and continue focused discovery rounds; do not limit clarification to one question. If diagram cannot be completed, report that one incomplete output; don't claim both succeeded. Missing AgentBoard prompts a storage-choice question before first local creation; do not skip consent.
