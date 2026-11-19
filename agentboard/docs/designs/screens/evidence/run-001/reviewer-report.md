# Independent Create-Screens review

**Status: verified_pending_review. Verdict: PASS within the frontend mock-data scope.**

Reviewer: `/root/screens_reviewer_finish` (distinct from implementation author `/root/screens_builder_finish`; prior run actors are recorded in orchestration.md). Read project Code Reviewer/Product Designer role files, all 15 User Stories, design topics and required Modern Web Guidance. Reviewer did not edit implementation; added independent tests/audits only under evidence.

Completed UTC: 2026-11-18T07:26:25.406179+00:00

- Source root: `frontend`
- Source fingerprint: `a773e87a417b92d37555940f4b5b822b096811ca6a0eca796e703a7c434f301e`
- Project requirements/roles fingerprint: `760a3640978ee58ee4e0ae0b32529f0c76e7307fb465757a1564c8eda4eea812`

## Scope and coverage

Reconciled the 12 inventory rows with all current frontend-relevant requirements: Projects and create/edit/switch (US-001/002), Overview/counts/blockers (US-009/012), Roles and forms (US-003/005), Tickets table/board/detail/create/edit/assignment/history and approval display (US-004/005/006/008/010/012), Documents/list/reader/editor (US-007/008), arbitrary retained revision comparison/restore/expiry (US-015), and Activity/filter/live-state/retention demonstrations (US-010/013/014). No required frontend screen or journey step is knowingly omitted.

US-011 and production portions of US-012–015 remain mocked. This verdict does not claim actual MCP tools, authentication, verified client approvals, Postgres transactions, durable logs, automatic server maintenance, real SSE, backend API execution or Compose deployment. Explicit preview labels and the coverage index preserve that boundary.

## Actual independently executed evidence

| Check | Result | Saved evidence |
| --- | --- | --- |
| TypeScript | PASS | reviewer-typecheck.log/json |
| Production frontend build | PASS | reviewer-build.log/json |
| Complete application browser suite | 14 passed | reviewer-ui.log/json; reviewer-tests/full-results.json |
| Additional independent regressions | 5 passed | reviewer-edge-ui.log/json; reviewer-tests/results.json |
| Nine-route axe-core audit | No detected A/AA violations | reviewer-a11y.log/json; reviewer-tests/axe-results.json |
| Representative computed contrast | 17 tested pairs pass | reviewer-contrast.log/json; reviewer-tests/contrast-results.json |
| Document output consistency | PASS | reviewer-output-consistency.log/json |

Commands, actual working directories, exit codes and UTC times are saved with the logs. Build was rerun after the final CSS changes; final UI runs include the final required-field markers and semantically stronger accessible-name assertions. Earlier failing outputs are not treated as current passes.

## Concrete findings and fixes

- **R-001 — Native dialog focus behavior:** removed redundant manual trap/return-focus code; kept native modal inertness, Escape, invoker return and dirty-close protection. Initial overstrict last-Tab assertion was rejected in favor of actual native semantics; both app and independent tests now pass.
- **R-002 — Failed draft lost via browser Back:** reviewer reproduced this with a saved failing test. Central history/hash guard now preserves the editor when discard is declined. Independent fifth regression passes; failed document save also creates no revision.
- **R-003 — Notice hidden by modal inertness:** shared OperationNotice exposes failures inside the active modal and suppresses the inaccessible background toast; failure-retention tests pass.
- **R-004 — Runtime regressions during guide integration:** a nested Hook and controlled-input event reset caused genuine suite failures. Builder corrected them; independent final 14-test run now passes, rather than reusing earlier green logs.
- **R-005 — Header/navigation semantics:** scoped sticky row/column headers and named keyboard-scrollable table regions preserve context; compact navigation keeps accessible names. Separate visual responsibilities reviewed across 44 TSX component/screen files, with one exported visual function per file.
- **R-006 — Focus contrast and forced colors:** contrasting inset primary focus and internal forced-colors outline preserve visible keyboard focus without violating the no-external-halo rule. Dropdown padding remains inside borders.
- **R-007 — Visible required indicators:** added aria-hidden markers only to required fields, with blocker marker conditional on Blocked. Refreshed captures show optional Purpose/Description unmarked. Exact actual accessible names are asserted via textbox roles; tests were not weakened to ignore accessibility.

No unresolved required implementation or guidance findings remain in the reviewed frontend scope.

## Rendered visual evidence and applicability

Inspected refreshed Projects, Roles, Overview, Tickets/detail/board, Documents/reader/editor/history, Activity, forms and compact history/ticket captures. Layout, typography, hierarchy, status-versus-approval separation, padded arrows and window adaptation are coherent with the draft profile. Builder capture harness refreshed 28 screen/state/window captures and recorded zero page runtime errors; all nine route renders were also independently exercised by audits/tests.

Parent separately performed actual native Chrome 200% zoom (not CSS zoom), saved browser zoom proof and scrolled the ticket inspector until Create ticket was visible. I inspected `chrome-ticket-editor-200-scrolled.png`. That evidence is retained as applicable: subsequent changes added semantics, validation notices, history guards and small required markers, not editor sizing, overflow or target dimensions. Regular 900/1280/1600 layout checks and final captures cover current code.

Axe reported `color-contrast` as incomplete, not a pass. Separate representative computed pairs meet normal text 4.5:1 (minimum measured 5.66), nontext controls 3:1 (border 3.65) and focus 3:1 (5.66). This is sample-based assessment, not exhaustive pixel checking or WCAG certification. Full screen-reader user testing, custom OS forced-color palettes and cross-browser compatibility are not claimed. Dark/system theme is a proposal, not confirmed scope for this run. Desktop only; no inferred phone support.

## Completion boundary

The independent verdict permits the orchestrator to assemble final evidence/latest.json and run the structural/freshness gate. It is not user design approval and does not authorize publishing, production integration or authoritative design-topic promotion. Any subsequent source or requirement change invalidates these fingerprints and needs proportionate re-verification.
