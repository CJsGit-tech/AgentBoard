# Concise design documents

Use ordinary Markdown in `docs/designs/`. Start at README: direction in one paragraph and a task → topic → required companion table. Index maximum 250 words.

Core topics: navigation-layout.md, visual-system.md, accessibility.md, interaction-states.md. Add feature topics only for actual story needs (for example tables-boards, document-history, activity-logs or approval-states). Do not force web-specific topics onto iOS apps.

Each topic starts with owner/version/status/date, **Purpose:** one sentence, **Related stories:** existing US IDs or Cross-cutting, and **Required context:** explicit relative links or None. Target 150–300 words; maximum 450, including tables. Use short rules, small comparison tables and concrete states. Remove repeated rationale; retain constraints, exceptions and unresolved decisions. Split a growing topic by concern and update navigation.

Keep shared interaction states authoritative in one file. Keep token values authoritative in design-tokens.json; reference instead of copying. Feature topics link required shared rules. Readers open the index, selected topic and named companions only; search headings for narrower context. Never claim a single topic is self-contained when dependencies are omitted.

Archive the prior design before migration outside active docs. Update design manifest path to docs/designs/README.md with layout=folder and matching version/status. Preserve tokens unless their values change. Folder artifacts must be edited as individual files, not through the single-file save_artifact command. Check story mappings, links and concise limits with check_outputs.py --strict. Structural validation does not prove design quality; manually check story coverage, exceptions and platform feasibility. No UI implementation is implied.

Target-platform gate: scope responsive layouts, components and preview/test dimensions to confirmed clients, input methods and deployment environment. Desktop web may require resizing and zoom without phone layouts. Record proposed viewport ranges explicitly; do not invent mobile, native or hosted targets.
