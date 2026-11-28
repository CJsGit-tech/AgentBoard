# Changelog

Notable changes to AgentBoard and AgentBuild, newest first. Dates are in Asia/Taipei.

## 2026-11-28 — Design Profile V5

The interface keeps the V4 colors and reads more clearly. It also adds per-project targets and reports. ([#2](https://github.com/CJsGit-tech/AgentBoard/pull/2))

### Added

- **Dashboard scorecard.** Completion, evidence coverage, run success and median time to last update are measured against the project's targets. Each tile shows ✓ when a target is met, or ◆ with the gap. The page summary names the missed targets.
- **Per-project targets.** `target_completion`, `target_evidence`, `target_run_success` and `target_median_hours` default to 100, 90, 95 and 4. Edit them in project settings → Dashboard targets. Existing projects read the defaults; no migration is needed.
- **Portfolio report** (`#portfolio`, under Workspace). This read-only view of every project needs no project selected. Export report downloads a CSV.
- **Read-only metrics API.** `GET /api/projects/<id>/metrics` and `GET /api/portfolio` accept `start`, `end` and `tz_offset`.
- **Charts.** These include gauges with target ticks, meter lists, pies, daily lines with a crosshair, a burn-up, a milestone timeline and a time-to-last-update bead plot.
  - Every chart has a Table view, keyboard-readable values and forced-colors support.
  - Chart colors were validated for color-vision deficiency.
- **⌘K / Ctrl+K quick switcher** for projects, documents and tickets. It only navigates.
- **Tickets board.** A status strip filters the board, empty lanes collapse into drop columns, and the Done lane shows its 6 most recent cards.
- **Assistant start state.** The connection status shows first. Suggestion chips fill the composer without sending.

### Changed

- **Look and structure.** Every page uses one header pattern. Cards are soft white with a 14 px radius, and the type scale is updated.
- **Sidebar.** The project switcher is a card, and the active page is a white pill. Project pages explain why they are locked when no project is selected.
- **Projects.** Cards show a status bar, a 7-day done sparkline and last activity, and can sort by Recent, Name or Progress.
- **Tickets.**
  - Ticket details open in a 560 px side panel. It has a property grid, Summary/Context/Outputs/Runs/History/Edit tabs and an acceptance checklist with Open proof.
  - Card actions (Move to, Open, Copy link) moved into a ⋯ menu. Moves still use the same revision and scope checks.
- **Documents.** Three columns: library, reader (16/27 prose, up to 720 px) and On this page.
- **Canvas.** The latest version is featured, and earlier versions are listed compactly.
- **Runs & activity.** Runs are grouped by day, with a linked-ticket chip and an agent timeline.
- **Roles.** Roles show a charter excerpt, a share meter and ranked Build/Bug bars.
- **Assistant.** The interruption notice is a one-line disclosure that opens the full text.

### Fixed

- A legacy green hover color on ticket cards.

### Known limits

- Tickets have no completion timestamp, so durations use the time to last update.
- No screen reader pass has been run on the V5 pages.
- The README walkthrough GIF predates V5.

## 2026-11-28 — Evidence workflows and performance

- **Proof on each criterion.** Ticket acceptance criteria can pin a Canvas version and link verified proof (a report section or a screenshot). Completion checks that required evidence is present.
- **Canvas viewer.** The viewer loads only the selected publication and records a verified screen count (migration 014). Screenshot thumbnails load as they come into view (migration 015).
- **Faster browser reads.** Reads are scoped to the project directory or one project, with ETag revalidation. The unscoped workspace read now returns a reload instruction (HTTP 410).
- **Tests.** New tests cover review invalidation, criterion evidence, the Canvas viewer and visual thumbnails.

## 2026-11-27 — AgentBuild for Claude Code

- Added the Claude Code edition of the AgentBuild skill (`skills/agentbuild-claude`).
- AgentBuild now requires verified ticket evidence before completion, and defines the sidebar gallery format for visual drafts.

## 2026-11-25 — 2026-11-26 — First public release and guides

- Published the source-only AgentBoard and AgentBuild release.
- Added bilingual READMEs (繁體中文 and English) with an animated walkthrough. The READMEs explain setup step by step, mark InApp Assistant as experimental, and include a software bill of materials.
