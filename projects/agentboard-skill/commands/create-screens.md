# Contract: Create-Screens <ProjectName>

## Purpose
Build all required product screens in the confirmed frontend stack with mock data, as one reusable frontend implementation for review.

## Preconditions
Required installed dependency: official `modern-web-guidance`. Follow `references/modern-web-guidance.md`; missing dependency/retrieval blocks verified completion.

Usable Product Vision, User Stories, Design Profile, confirmed frontend stack, target platform and deployment constraints. Reuse recorded decisions; do not request them again. Resolve genuinely missing stack choices before dependent implementation.

## Owner
Orchestrator coordinates a real builder and a distinct independent reviewer using project `agents/frontend-programmer.md` and `agents/code-reviewer.md`. Both consult `agents/product-designer.md`; follow `references/screen-verification.md`. This pair is required for this command.

## Required context
Follow SKILL.md’s Confirmed platform and deployment policy and `references/create-screens.md`. Read the design/story indexes, architecture source layout and stack decisions first, then the required files for each screen batch. Inspect existing frontend source, dependencies and components. Read `references/screen-verification.md` and the actual project role files.

## Execution
1. Verify the Modern Web Guidance dependency and read its SKILL.md. Search/retrieve applicable patterns before web UI implementation; record guidance selection and compatibility assumptions. Dispatch a real builder and later a separate non-author reviewer as specified in the verification reference; record actual invocation identities. Derive a complete screen inventory from all current stories and the Design Profile. Record screen/route → story/feature → key states → source path → review/verification state in `docs/designs/screens/README.md`. Reconcile missing or conflicting requirements; do not silently omit screens or choose one journey as the default scope.
2. Resolve the canonical frontend source location from the repository and architecture. Reuse it or scaffold it once using the confirmed frontend stack and installed component library. Do not create a disposable HTML/JS app or copy frontend source into review-round folders. If the required toolchain is unavailable, resolve setup within authorization or report a blocker; never substitute a different stack silently.
3. Build all inventoried screens and working navigation with shared mock records and stable identities. Work in related batches while keeping full coverage as the completion target. Demonstrate key create/edit/read/status, loading, empty, error and other story-specific states with local simulation. Keep production integrations outside this command.
4. Separate mock fixtures and data adapters from visual components. Each meaningful custom visual component MUST have its own file, derived from feature/story responsibilities, even if small or used once. Screen files compose components; reuse existing library primitives and shared feature components. Review the feature → component → file map against actual source.
5. Render all required screens and walk the major user flows and return paths. Verify state consistency, keyboard access, and responsiveness for the confirmed target/deployment environment. No external focus halos; keep keyboard focus visible inside controls. Dropdown icons must be padded entirely inside borders without text collisions. Fix failures; record unverified cases honestly.
6. Have the reviewer critique source and rendered screens against retrieved Modern Web Guidance. Send applicable findings to the builder for improvements, re-review each fix, and save the guide/finding/fix/test matrix. Do not treat retrieval itself as a compliance pass. Run required automated checks and save reproducible commands, logs, test results and captures. Have the independent reviewer reconcile full coverage, rerun checks, inspect rendered screens and write a pass/fail report. Send findings to the builder and reverify fixes. Run `scripts/check_screen_evidence.py --project <project>` on the final source; missing/failing/stale evidence blocks completion.
7. Follow `references/modern-web-guidance.md#mandatory-scan-and-feedback-resolution-policy`: its mandatory per-turn scan/reviewer/fix loop is a completion requirement, not an optional report. `references/screen-verification.md` owns role separation and final evidence requirements.
8. Update the coverage index and save representative screen/state captures under `docs/designs/screens/captures/`. Continue until all required screens are implemented and reviewed, or explicitly report blockers and incomplete items. Only after the completion gate passes, report verified_pending_review (human approval is separate). Present one coherent design pending_review; alternatives only on request. Do not declare full completion from a single working screen.
9. Revise the same source files on later calls. Preserve history via repository version control or targeted archives before replacement; do not duplicate the app per review round. Only after explicit user confirmation promote screen links into authoritative design topics and update relevant design metadata.

## Output artifacts
- Canonical frontend source in the project's confirmed source layout and frontend stack.
- Separate mock fixtures/adapters and meaningful component files.
- `docs/designs/screens/README.md`: complete screen coverage and component/file maps, run instructions, limitations and pending_review status.
- `docs/designs/screens/captures/`: required screen/state review evidence; no duplicated application source.
- `docs/designs/screens/evidence/<run-id>/`: saved actual automated outputs and independent reviewer report; `evidence/latest.json` binds coverage, identities and checks to the final source fingerprint.

## Acceptance checks
- Every required screen and key flow is accounted for and implemented; no required navigation placeholders or silent scope reduction. Smaller scope only on explicit user request, labeled partial coverage.
- Confirmed frontend stack and one canonical implementation; existing code/components reused, mock data isolated.
- Each meaningful custom visual component has its own file; screen and feature mappings match source.
- Rendered target-platform checks, internal focus indicators and padded dropdown icons verified; captures and unverified limitations recorded.
- Appropriate frontend build checks and `check_outputs.py --strict` pass. Structural checks do not prove full screen coverage; review it separately.
- A real distinct reviewer passes the final implementation; build/type/UI/consistency checks and saved evidence gate pass with no unresolved required items.
- No real backend, product-agent execution, production deployment, new implementation command or automatic approval implied.

## Persistence updates
Track screen coverage and review evidence locally without marking design artifacts approved. Preserve confirmed storage mode. Update authoritative design links/metadata only after user confirmation; no automatic remote writes.

## Failure handling
Keep useful work and report precise toolchain, scope or requirement blockers with affected screens. Missing tooling is not permission to switch stacks. Do not claim completion when required screens or verification are missing. Without separate reviewer execution, saved evidence or mandatory checks, report partial/blocked; self-review cannot satisfy independent validation.
