# Design Profile — AgentBoard

> Owner: Product Designer | Version: 0.1.0 | Status: draft | Last Updated: 2026-11-18
> Based on: Product Vision v0.1.2; User Stories v0.1.2; Technical Architecture v0.1.4

**Purpose:** Specify a clean, minimal workspace for inspecting progress and operating on projects, tickets, documents and agent-reported outputs.

**Confirmed direction:** Clean/minimal presentation; effective progress visualization; table and board views for understanding and operating on work. Layout, palette, tokens and defaults below are design proposals, not approved screens or implemented behavior.

## 1. Design Direction

**Quiet workspace, visible exceptions.** Neutral surfaces, strong text hierarchy, restrained blue actions and clearly labeled operational states. Prioritize useful records over decorative cards or dashboard chrome.

| Surface | Design choice | Why |
| --- | --- | --- |
| Main work area | Table first; alternate board | Precise inspection plus visible task flow |
| Project summary | Counts and one horizontal status distribution | Understand work without reading every ticket |
| Selection | Right-side inspector on wide screens | Inspect a record without losing list context |
| Documents | Title list, outline, selected content/history | Reveal only the output needed |
| Activity | Compact event rows with filter chips | Agent + ticket + action + time remain readable |

Avoid decorative gradients, giant KPI cards, donut charts for four task counts, nested card grids, animated counters and invented agent/productivity scores. The architecture diagram is a structural reference, not an application color/theme mandate.

## 2. Design Principles

1. **Operate where you inspect.** A selected row/card exposes its details and relevant actions without another dashboard hop.
2. **Status and approval are independent.** Keep Needs approval separate from Planned/In Progress/Blocked/Done in every view.
3. **Show measured facts.** Counts describe saved tickets; reported events do not prove agent execution or full external capture.
4. **Keep context on demand.** Default views show identity and operational fields; long documents, revisions and request payloads open explicitly.
5. **Keep reading stable.** Live updates must not move the selected row, erase a draft, or scroll someone away from an event.

## 3. Information Architecture & Navigation

```text
Project picker / project list
  Selected project
    Overview
    Tickets       [Table | Board]
    Roles
    Documents
    Activity
```

- Sidebar shows the selected project's name and those five destinations. Project switching is always visible; do not mix records across projects.
- Main header: project context → page title → primary action. Use one prominent primary action per surface.
- Ticket/document detail URLs carry project and record identity; reopening a link restores context or shows missing/unavailable state.
- Project list creation/editing and Roles are ordinary record management. “Roles” means responsibilities, not running agent processes.
- Global search, command palettes, agent launch controls and connection-management screens are not introduced by this profile. Use existing filters and project navigation first.

## 4. Visual Hierarchy & Information Density

| Level | Content | Treatment |
| --- | --- | --- |
| 1 | Project/page identity | 20–24 px heading; no oversized hero |
| 2 | Primary work surface | Table/board/document; fills most viewport |
| 3 | Status, owner, priority, approval | Compact labeled fields |
| 4 | Times, IDs and provenance | Muted text; exact value on inspect |

Default table rows are 44 px minimum and may grow for wrapped content. Board cards use title, owner, priority, updated time and separate approval badge. Limit preview text to two lines; opening detail reveals the full value. Show a short UUID prefix only as secondary identification; it is not a new stored ticket code or a planning US-### ID.

### Progress Visualization

- Four labeled counts: Planned, In Progress, Blocked, Done. Each count opens the corresponding ticket view using the existing status filter.
- One horizontal stacked bar encodes those same counts, with text legend and an accessible count table. Equal units represent tickets, not effort.
- Show Done/total as task completion only. Do not call it overall product completion or display 100% for an empty project.
- Needs approval appears as a separate count/badge, not another bar segment or task column.
- No burn-down, throughput, time-series or live-agent utilization charts until supporting data and requirements exist.
- Label overview values **Project totals**. Do not imply that they reflect local list filters unless the backend provides matching aggregates.

## 5. Progressive Disclosure

| Initially visible | Open on demand |
| --- | --- |
| Ticket title/status/owner/priority | Description, blockers, linked documents, activity, pending request diff |
| Document title and update time | Content, heading outline, versions and comparison |
| Agent activity summary and labels | Event provenance, exact timestamp and related ticket |
| Approval badge | Proposed changes, request state and instruction to continue in Codex/Claude |

Document outlines support selective human viewing of Markdown headings. They do not imply new section-level MCP retrieval or automatic import of skill-generated files. Linked documents are the available output surface; minimal activity logging is not storage for arbitrary full tool results.

## 6. Color Palette & Semantic Roles

Values are proposed implementation tokens in [design-tokens.json](design-tokens.json).

| Role | Light | Dark |
| --- | --- | --- |
| Background / surface | #F7F8FA / #FFFFFF | #111722 / #1B2330 |
| Text / muted text | #18212F / #526071 | #ECF0F6 / #AAB6C7 |
| Decorative border / control boundary | #D4DAE3 / #7B8798 | #465368 / #748299 |
| Primary action / on-primary | #315FD3 / #FFFFFF | #A8BEFF / #172348 |
| Selected surface | #EAF0FF | #26375A |

| State | Label and symbol | Light text / background | Dark text / background |
| --- | --- | --- | --- |
| Planned | Planned + empty circle | #526071 / #EEF1F5 | #AAB6C7 / #293342 |
| In progress | In progress + partial circle | #274EA5 / #EAF0FF | #BCD0FF / #24365B |
| Blocked | Blocked + warning triangle | #A52C36 / #FDECEE | #F5AEB5 / #43252C |
| Done | Done + check | #196442 / #E6F4EC | #8ED4AE / #183C2D |
| Approval | Needs approval + shield | #805000 / #FFF4D6 | #F4CF83 / #3D3019 |

Use color for meaning, not decoration. Small text requires 4.5:1 contrast; meaningful controls/focus/chart segments require 3:1 against adjacent surfaces. Decorative dividers need not carry the control-boundary meaning. Chart legend labels use normal text tokens, not colored tiny text.

## 7. Typography

- System sans-serif: system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif. No remote font dependency.
- Base 16 px; table/body compact 14 px; secondary timestamps 12 px; section headings 18–20 px; page titles 24 px.
- Body line height 1.5; headings 1.25; weights 400/500/600. Use tabular numerals for aligned counts and times.
- System monospace only for UUIDs, request IDs and code/diff content. Do not style ordinary agent activity like terminal output.
- Absolute times include timezone on inspection; relative labels expose the exact timestamp accessibly, not hover-only.

## 8. Layout, Spacing & Responsiveness

| Width | Behavior |
| --- | --- |
| ≥1280 px | 216 px sidebar; fluid work area; optional 440 px detail inspector |
| 960–1279 px | 200 px sidebar; detail becomes overlay so tables remain usable |
| 768–959 px | Collapsible navigation; one focused content surface |
| <768 px | Full-width details; table becomes labeled rows; board shows one selectable status column |

Use 4/8/12/16/24/32 px spacing; 24 px main gutter on desktop, 16 px narrow. Section separation uses whitespace and thin borders rather than another enclosing card. Radius 6 px for controls, 8 px for panels. Reserve shadows for overlays/popovers.

Board columns are exactly the four task statuses. Each column paginates independently; show loaded/available context and a Load more control. Do not present the first page as the entire column. Preserve the selected table/board preference locally; record data remains authoritative in Postgres.

## 9. Components & Interaction States

| Component | Default and operation | Failure / important state |
| --- | --- | --- |
| Ticket table | Title, status, owner, priority, approval, updated time; row opens inspector | Keep selection and scroll on refresh; explicit failed-load state |
| Board | Status columns; same data/actions as table | Status menu works without dragging; no drag-only interaction |
| Editor | Labeled fields; primary Save; explicit unsaved indication | Inline validation retains input; navigation warns before discarding |
| Blocker control | Status change to Blocked reveals required reason | Failed save keeps saved status and draft reason visible |
| Approval details | Read-only proposed diff, request ID and state | No approve button; copy request ID and continue in a capable client |
| Document history | Current plus up to three previous versions; timestamp and comparison | Pruned version is unavailable; never substitute another |
| Restore/delete confirmation | Explain content/version impact before explicit human action | Agent restore still follows client approval; web action does not add a second agent gate |
| Activity table | Agent, ticket/title when present, action, time, outcome, labels, provenance | No full prompt/tool payload by default; do not claim exhaustive external capture |

### Shared States

- Hover: subtle surface change. Focus: visible 2 px primary ring with 2 px offset. Pressed: selected surface, not motion-dependent feedback.
- Loading: retain layout; reserve skeletons for initial loads. Refresh retains prior values with an updating indicator.
- Empty: explain the absence and offer a relevant create action. No tasks is not project completion; no retained events is not proof no work happened.
- Error: show action-specific message and retry. Never render unavailable data as zero counts.
- Success: update canonical data and acknowledge once. Disable repeated submission while saving; honor backend idempotency/revision errors.
- Conflict: show newer saved version and the user's draft separately; require review before resubmission.
- Reduced motion: remove transitions. Otherwise use 120–180 ms opacity/color changes; no animated metric counting.

### Activity and Live Updates

Filters: project context, ticket, observed agent/client, type, labels, outcome, provenance and time. Default last 24 hours is **proposed**; cap available history at the confirmed 30 days. Clicking an agent/event label can apply its filter; do not imply a complete live-agent roster.

When reading older rows, accumulate a “new events” control instead of moving the viewport. Batch screen-reader announcements. On disconnect, retain visible data, show stale/live state and offer retry. Reconnect from retained event IDs; if history expired, explain the gap and resync. Distinguish **reported** external events from **observed** AgentBoard operations in text.

## 10. Accessibility

- All actions, filters, column selection and status changes are keyboard-operable. Do not require drag, hover or color recognition.
- Use native table semantics for tables; explicit headings/lists for boards. Clickable rows retain a real title link and labeled action button.
- Focus enters dialogs predictably, stays inside modal overlays, and returns to the trigger on close. Escape never silently discards an unsaved draft.
- Minimum 24×24 px targets; propose 36 px controls and 44 px touch targets. Keep sufficient spacing around small desktop icon controls.
- Status, approval, provenance and chart counts have text equivalents. Diffs identify additions/deletions with signs and labels, not red/green alone.
- Support 200% zoom without losing actions; allow necessary horizontal table/diff scrolling with clear labels. Respect reduced motion and text scaling.
- Token contrast checks establish color pairs only; browser keyboard, screen-reader and zoom checks are still required on implementation.

## 11. Themes

Provide Light / Dark / System, with System as the proposed default. Theme choice is local UI preference; it does not affect data, approval or retention. Use semantic tokens in both modes, and switch without clearing forms or changing chart meanings.

## 12. Screen Inventory & Story Mapping

Routes are proposals, not new backend endpoints.

| Screen / route | Primary task | Stories | Important states |
| --- | --- | --- | --- |
| `/projects` | Create, identify and reopen projects | US-001, US-002 | Empty, duplicate names, failed save |
| `/projects/:p/overview` | Inspect totals, blockers and next work | US-009, US-012 | No tasks, unavailable counts, pending badge |
| `/projects/:p/tickets` | Table/board; create, prioritize and assign | US-004, US-005, US-006 | Unassigned, blocked, saving, conflict |
| `/projects/:p/tickets/:t` | Details, linked outputs and recent changes | US-006, US-008, US-010, US-012 | Several pending requests, stale approval, expired activity |
| `/projects/:p/roles` | Define responsibilities | US-003, US-005 | Empty, validation, assigned role |
| `/projects/:p/documents` | Find/create product documents | US-007 | Empty, missing title/content, unsaved draft |
| `/projects/:p/documents/:d` | Read/edit, compare and restore | US-007, US-008, US-015 | Version unavailable, conflict, retention notice |
| `/projects/:p/activity` | Filter and review agent/API activity | US-010, US-011, US-013, US-014 | Live/disconnected, reported/observed, 30-day gap |

US-011 is also a cross-cutting source of records/notifications, not a fake agent-control screen. Agent approval in US-012 stays in Codex/Claude. Direct record actions in the web UI remain explicit human operations.

## 13. Design Tokens & Handoff

[design-tokens.json](design-tokens.json) contains proposed semantic colors, typography, spacing, dimensions and motion. It is a specification, not an implemented component library.

| Implementer | Handoff |
| --- | --- |
| Frontend | Match table/board behavior; draft preservation; keyboard support; semantic state tokens |
| Backend / API | Supply canonical counts/pagination; keep status and derived approval distinct; enforce mutations/history |
| Integration | Surface pending/unsupported client approval accurately; never convert reported activity into verified execution |

Use existing [contracts](../technical-architecture/contracts/README.md). Do not silently extend API fields to satisfy a layout. The outline, diff rendering and responsive arrangement are frontend presentation choices.

## 14. Open Decisions

| Decision / gap | Owner | Proposed resolution |
| --- | --- | --- |
| Table first, palette, System theme and 24-hour activity default | Product owner | Review this visual direction; all are draft proposals |
| Global priority sorting across paginated tickets | Architect/backend | US-004 requires sorting; current OpenAPI lacks an explicit sort parameter. Define server ordering/contract before implementing it; do not sort only the visible page and imply global order |
| Approval-only ticket filtering | Architect/backend | Current query contract does not declare it. Show the badge/count now; add drill-down only after contract agreement |
| Filtered overview aggregates | Architect/backend | Keep project-total labels until an aggregate filtering contract exists |
| Screen-level validation | Designer/frontend | Build representative Overview, Ticket table/board, Document history and Activity states; test keyboard/zoom and dense real data before implementation sign-off |

No user story, architecture contract or application code is changed by this profile. Visual values remain draft pending review.
