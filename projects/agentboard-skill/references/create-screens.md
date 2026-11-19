# Create all product screens once

## Coverage and selective context

Default scope is every screen and important UI state required by the current Product Vision, Stories and Design Profile. Start with their indexes and derive a compact coverage table; do not load all detailed files for every edit. Open relevant story/design files per batch. A connected journey is a verification unit, not a reason to omit the rest of the product. Users may explicitly request a smaller scope; record incomplete product coverage rather than treating it as full completion.

Keep `docs/designs/screens/README.md` concise, linking detailed per-feature notes only if needed. Include screen/route, story/feature IDs, key states, implementation path, review status and verification limitations. Maintain a feature → meaningful component → file/library-import map. Reuse this inventory on later calls instead of rediscovering scope. Never add a product feature just to fill navigation.

## Canonical source and mock data

Use the confirmed frontend stack and architecture source layout. Reuse existing source and installed UI primitives. If absent, scaffold the intended frontend once; resolve missing toolchain rather than silently creating a different-stack throwaway preview. For AgentBoard, the confirmed stack is React/Vite and the target is desktop browser on a personal computer with local Docker Compose. This example does not set other projects' stack or platform.

Build shared shell, navigation and feature components, then related screen batches. Keep shared mock records, identities and local edits consistent across navigation. Separate fixture data and adapters from UI so screens do not embed or depend on fixture specifics. Simulate key actions with clearly labeled local behavior; do not implement real services merely to make screens clickable. Production service integration, deployment and additional command stages are outside this scope.

Frontend source stays in its canonical directory, not in `docs/designs/` or per-review copies. Design review evidence lives at:

```text
docs/designs/screens/
  README.md                 # inventory, coverage, source links and review state
  captures/                 # screen/state captures; no application source
```

## Required component boundaries

Derive meaningful visual responsibilities from product features and acceptance criteria. Each custom component with independent domain meaning, behavior, states or reusable visual responsibility MUST have its own implementation file, even if used once. StatusBadge and ApprovalBadge are distinct; combining them in Badges does not satisfy the rule. Screen files compose feature components; entrypoints wire the app. Shared nonvisual helpers and fixtures live separately.

Reuse an existing component in its existing file. Do not duplicate or wrap every library button, icon or label simply to create files. Organize by feature where useful. Review actual source against the component map: paths exist, components match responsibilities, and independent visual components are not bundled into one implementation file. A successful build alone does not pass this review.

## Review without duplicate work

Revise the same implementation. Preserve history with version control or targeted archives before replacements; no whole-app copying into numbered rounds. Reuse existing evidence for unchanged screens, run checks appropriate to changed behavior and shared dependencies, and verify affected flows. At completion, every required screen needs actual render evidence and coverage review. Follow the mandatory per-turn scan and feedback-resolution policy in `modern-web-guidance.md`.

Check layouts, resize/zoom behavior and input methods appropriate to confirmed target platforms and deployment context; web does not imply phone layouts. All required navigation works. Verify shared state, error/empty/loading states and important story-specific exceptions. Record missing checks and blockers explicitly. Screens remain pending_review until human confirmation; internal screen index/source links are allowed before review, authoritative design-topic links require confirmation.

## Control borders and keyboard focus

No external focus halos: use a visible inset ring or internal border treatment, never an outward focus shadow or positive-offset outline. Keep keyboard focus visible. Dropdown icons stay fully inside borders with internal edge padding and reserved text space. Use supported library styling APIs. Verify rendered focus, long values, disabled/error states and targeted viewport/theme/zoom cases where applicable; CSS alone is not proof. Record unverified cases.

## Mandatory completion gate

Follow `screen-verification.md`: real builder and independent reviewer using the project agents folder, actual automated checks, saved evidence and final-source validation. Self-review or narrative claims cannot satisfy the gate.
