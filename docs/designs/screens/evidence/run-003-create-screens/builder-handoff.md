# Create-Screens builder handoff · run 003

Builder: `/root/create_screens_builder_003`, using agents/frontend-programmer.md and product-designer.md. All 15 current story files reconcile with the 12 existing screen/state inventory rows. Canonical React/Vite/TypeScript frontend reused; no duplicate app or scope expansion.

## Required corrections

| Finding | Builder change | Regression evidence |
| --- | --- | --- |
| R-003-01 | ActivityFeed accepts optional agent/label filter callbacks; ActivityScreen supplies them. Native buttons update existing filters; other feed contexts keep noninteractive text. Minimum 24px targets reuse inset focus. | Existing activity UI test now clicks both actions and asserts corresponding filter values. |
| R-003-02 | ProjectCard/RoleCard Edit buttons have descriptions linked by per-instance useId to visible project title/role heading. Visible Edit labels remain. | Existing project/role UI tests assert distinct accessible descriptions. |

Six changed source/test files: ActivityFeed.tsx, ActivityScreen.tsx, ProjectCard.tsx, RoleCard.tsx, styles.css and tests/screens.spec.ts. Targeted pre-edit backups in builder-before/frontend/. No authoritative design links or user approval changed.

## Actual checks

Saved builder-typecheck/build/ui JSON metadata and logs record exact commands, working directory, UTC completion and exit 0. All 14 browser tests passed in installed Chrome; shared states, flows, keyboard containment, desktop widths and the new regression assertions run against current source. builder-ui.config.cjs redirects all test outputs into this run, preserving previous evidence. builder-check.py reproduces checks using temporary Node24.

Mandatory end-of-turn scan: builder-legacy-scan-raw.json; 0 findings over 52 deterministic rules/38 guides. Command/UTC/exit metadata in builder-legacy-scan.json. Narrow static scan does not prove broad UI quality; independent review remains required.

Source fingerprint: `0043d7819dac8306a1b0b6fc21068492c3d53db478981e64d71355f4fb398bad`.
Context fingerprint: `760a3640978ee58ee4e0ae0b32529f0c76e7307fb465757a1564c8eda4eea812`.

## Guidance and limits

Read installed dependency and reuse previously retrieved unchanged dialog, responsive-table, forms and accessibility guidance from run-001/modern-web-guidance-guides.md. Accessibility guide requires native actions and contextual descriptions for identical Edit controls; fixes use these patterns. Keep desktop scope, inset focus/forced-colors fallback and internally padded select arrows; no inferred phone layouts or experimental APIs added.

Reviewer notified with evidence paths and requested to inspect changed Activity render and target descriptions. Existing unchanged captures require explicit applicability review; Activity must be refreshed for its new actions. Builder does not author independent verdict or latest.json. Real MCP, verified client approval, durable backend/storage, production Compose deployment, full assistive technology and cross-browser conformance remain unverified/outside mocked frontend scope.
