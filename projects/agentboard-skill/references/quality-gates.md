# Quality gates

Run these checks for every drafted artifact. Automated checks catch structural problems; semantic checks require judgment.

## Product Vision

- Exactly three content sections: Product Overview, PainPoints, Features & Value Proposition.
- Product Overview is one paragraph describing the product, audience, and intended value.
- PainPoints uses bullet points for concrete user problems.
- Features & Value Proposition gives each feature its own bold line followed by one or more value bullets; no table.
- Keep owner, version, draft status, and real date metadata. Label assumptions inline; do not add goals, scope, risk, or use-case sections.
- Refer to features by name downstream; existing IDs remain preserved in revision history.

## User Stories

- Stories explain **user need/value** rather than prescribe code architecture.
- Each `US-###` title is followed by exactly Story (one description bullet), Acceptance Criteria (testable bullets), and Associated Features (exact feature names from Product Vision as bullets).
- Keep document metadata; omit index, priorities, dependencies, notes, open questions, and scope/coverage sections. Resolve blocking questions in conversation.
- Criteria cover successful, empty/error, and permission/edge paths where relevant.
- Avoid abstract criteria such as "intuitive" or "fast" without a definition.

## Technical Documents

- Applicable REST/MCP/data contracts and labeled JSON examples are linked from concise topics. validate_contracts.py passes against actual operation/tool bindings; structural conformance is not proof of runtime authorization or cross-record constraints.

- Shared/web/iOS profile and optional-topic decisions confirmed before scaffolding; use architecture-document-profiles.md.
- Selected files satisfy their catalog content contracts; no skeleton markers, empty required sections or unexplained N/A.
- Every story acceptance criterion maps to actual design content; review cross-file consistency, diagram alignment and verified technical evidence.
- Documented review has no unresolved critical/blocking findings. Scripts prove structure, not semantic correctness or human approval.

- Multiple discovery rounds completed; deployment, stack choices/tradeoffs, third-party providers, integrations, and operational needs collected before writing; readiness brief confirmed or explicitly delegated.
- Diagram matches the module-oriented reference layout and visual grammar, with actual functional modules, boundaries, protocol labels, configuration flows, and persistence. Example technologies are not requirements.

- Explicit environment/deployment/SDK constraints or labeled assumptions.
- Technologies selected with rationale and meaningful alternatives, without invented compatibility claims.
- Clear component boundaries, data flows, deployment, nonfunctional requirements, security/privacy, and FE/BE folder structures.
- API contracts and storage are included only when relevant; write `N/A` with reason otherwise.
- The `system-architecture.svg` is well-formed SVG with meaningful labels, boundaries, and directional flows, consistent with the technical document; inspect/render visually if tools allow.

## Design Profile

- Design direction is concrete and discriminative, not "modern clean" alone.
- Color semantics and light/dark behavior (where applicable) are coherent; tokens are valid JSON if produced.
- Typography, spacing, density, hierarchy, layout, navigation, accessibility, interactions, and progressive disclosure are addressed.
- Distinguish design specifications from implemented screens. Frontend Programmer reviews feasibility, not visual taste alone.

## Plain Folder Navigation

- One canonical file per story/topic; README links every file, and story navigation includes features.
- Open relevant files selectively; no duplicate combined source or custom context engine.
- validate_project.py checks folder IDs, filename consistency, local file links, story format and architecture coverage.

## Cross-document review

- Vision features and user value map to user stories; establish unresolved MVP boundaries in the stories workflow.
- Architecture and design do not contradict supported platforms, performance/accessibility constraints, or each other.
- Unknowns and decisions are visible and assigned; no critical assumption silently turns into fact.
- No approval, validation, agent execution, or remote sync is claimed without evidence.

## Optional structural validation

```sh
python3 scripts/validate_skill.py
python3 scripts/validate_project.py --project ./workspace/my-product
```

These validate filenames, metadata, JSON, and SVG. They do **not** prove product correctness.

Target-platform gate: scope responsive layouts, components and preview/test dimensions to confirmed clients, input methods and deployment environment. Desktop web may require resizing and zoom without phone layouts. Record proposed viewport ranges explicitly; do not invent mobile, native or hosted targets.
