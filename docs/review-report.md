---
name: "Planning Review — AgentBoard"
description: "Traces AgentBoard stories to implementation and records release evidence and remaining verification."
kind: "document"
tags: ["feature:progress-tracking", "concern:retention", "concern:reliability", "concern:authorization"]
---

# Planning Review — AgentBoard

> Owner: Code Reviewer | Version: 0.1.11 | Status: draft | Last Updated: 2026-11-19
> Review mode: independent source and release-evidence trace

## Scope & Evidence

This report preserves the prior focused source re-review of four implementation findings and adds a full Vision-to-stories trace with the release evidence currently recorded below. The story-level disposition distinguishes source coverage from runtime evidence.

| Artifact | Version | Status | Evaluated / unavailable |
| --- | --- | --- | --- |
| Product Vision | 0.1.5 | draft | Feature names and scope read for traceability; product completeness and prioritization were not independently reassessed. |
| User Stories | 0.1.5 collection | draft | Active story index and US-001–US-017 read for feature association and acceptance-criteria trace. |
| Technical Architecture | 0.1.2–0.1.8 topics | draft | Index and relevant API, MCP, approval, history, activity, deployment and AgentBuild topics read; source paths inspected for mapped behaviors. This was not an exhaustive schema conformance audit. |
| Design Profile | 0.1.5 index; 0.1.2 topics | draft | Index and relevant navigation, table/board, progress, history, activity, approval and artifact-operation topics read. Independent visual review was not performed in this pass. |
| Implementation source | Current source at review time | In progress | Source traced against the full active story set, with focused inspection of prior findings and the atomic TicketCreate path. Runtime results below are run-owner evidence; no runtime actions or tests were performed by this reviewer. |

Runtime results below are the saved run-owner summary in this report. I independently inspected the active stories, architecture/design indexes and relevant implementation paths, but did not rerun the runtime checks. Native GUI approval verification remains outstanding.

## Prior focused re-review verdict

**reviewed_with_no_blockers**, limited to the four previously reported findings listed below. This is not a human approval or overall release verdict; browser and real-client evidence remains outside this re-review.

## Findings

| ID | Severity | Artifact / reference | Finding and evidence | Recommended resolution | Owner |
| --- | --- | --- | --- | --- | --- |
| — | — | — | No open findings in this focused re-review. Prior findings and their current disposition are recorded below. | — | — |

## Traceability & Coverage

- **R-001 — Connected activity retention: resolved.** US-014 and the architecture define the server receipt time as the authoritative 30-day clock. The connected activity screen now uses the server-retained collection without reapplying the mock adapter’s `occurred_at` cutoff (`frontend/src/features/activity/ActivityScreen.tsx:27-28`).
- **R-002 — Activity cursor tie ordering: resolved.** The activity query sorts by `received_at DESC, id DESC`, matching its strict tuple `<` cursor predicate (`backend/app/main.py:159-174`). Tied timestamps therefore continue after the last returned ID rather than revisiting earlier IDs.
- **R-003 — Floating base-image references: resolved.** The PostgreSQL, Python, and Node images used by the current Compose and backend Docker build include SHA-256 digests (`compose.yaml`; `infra/backend.Dockerfile`). Dependency lock/install behavior was not otherwise reviewed.
- **R-004 — Approval payload retention: resolved in current source.** Normal terminal transitions clear `proposed_changes`; MCP serialization derives an expired status from `expires_at` and redacts the payload even before maintenance runs (`backend/app/mcp/operations.py:130-141, 268-273, 323-342, 405-417, 752-754`). Maintenance then expires and clears pending requests and prunes terminal requests after the configured retention period (`backend/app/services/activity.py:53-68`). This finding concerned retention/read exposure and did not indicate an approval bypass.

The prior focused pass did not perform a full Vision-to-all-stories trace. This supplement supplies that trace below. It does not independently reproduce runtime checks or validate every API/MCP schema. The technical architecture explicitly defers automatic AgentBuild launch/readiness integration; this is recorded as deferred scope, not treated as a missing release requirement.

## Risks & Open Decisions

- The run summary covers key persisted browser paths and SDK-mediated MCP operations. It does not establish every story acceptance criterion or native GUI approval support. See the full trace below.

## Next Actions

1. Complete the remaining full-journey and retention checks and preserve their evidence.
2. Close the client-compatibility gate only after the named real clients, including their approval UX, have been exercised.


## Local runtime evidence

| Check | Observed result |
| --- | --- |
| Docker Compose | Postgres, migrations, FastAPI, maintenance and the loopback web service started. Proxied health returned ready. |
| REST with Postgres | Pairing, repeat create keys, project-scoped ticket ownership, tag filters, upload filename, current plus three prior document versions, stale-edit detection, links, progress and activity passed. Cross-project document read, edit and listing were isolated. A delayed occurrence remained visible while its receipt was recent, and a 31-day-old receipt was excluded. Both a timezone-free reconnect cursor and an expired UTC cursor caused resync after the [T-025 repair](tickets/T-025-resync-timezone-free-activity-cursors.md). A separate API process with an unreachable database returned HTTP 503. |
| Connected desktop browser | Chrome at 1280 × 900 paired, created a project and role, reviewed and saved an exact tagged Markdown upload with BOM and CRLF frontmatter preserved, reopened the rendered document after reload, edited and restored it as a new revision, created an assigned blocked ticket in one request, and linked the document from the ticket inspector. A pending MCP request updated the separate approval badge live without changing task status. A delayed activity report appeared live at 1280 pixels. The Activity page fit at 900 pixels without horizontal page overflow. A second run verified a retained project draft after a simulated save HTTP 503, a successful retry, and keyboard navigation and tag selection at Chrome’s actual 200% page zoom. At 200%, the 1280-pixel test viewport measured 640 CSS pixels, devicePixelRatio 2, and scrollWidth 640. Chrome 158.0.8127.36 ran on macOS arm64. After backend and maintenance recreation, a new browser session reopened the restored document and read the original blocked ticket with its separate approval flag. |
| Mock frontend regression | TypeScript, production bundle and 14 existing mock browser checks passed. |
| MCP protocol | 31 tools discovered with the Python MCP SDK on protocol 2025-11-25. Auth rejection, read/create, pending without elicitation, explicit accept, decline, retry replay and terminal payload clearing passed over authenticated HTTP. The local Claude Desktop stdio connection also passed discovery, Create/Read, unregistered tag rejection, pending, accept, decline and replay through the SDK. |
| Installed client discovery | Codex app-server 0.169.0-alpha.11.1 discovered all 31 tools, created a synthetic project and ticket, read it at revision 1, accepted an update through `mcpServer/elicitation/request`, reconnected and read revision 2, then declined another update without changing state. An intervening edit also proved that an older accepted prompt could not overwrite a newer revision. Duplicate document creation, document revision listing, and activity append passed. Approval answers were synthetic protocol responses. Claude Code 2.1.327 discovered all 31 tools and executed real AgentBoard project Create/Read. Its model loop used a deterministic localhost Messages mock; no provider call was made. Both clients used temporary settings and synthetic records. |
| Recovery | Created a Postgres backup and restored it to a temporary database. The migration revision and row counts were readable after restore. |

The graphical desktop approval dialogs still lack direct verification. The disposable graphical test helper passed transport, approval-boundary, and cleanup checks. Browser evidence covers the local Chrome environment and the journeys listed above. The previous visual approval still applies to its recorded mock scope. The AgentBuild automatic launch path remains deferred. [Graphical profile checks](evidence/client-approval/graphical-desktop-status.md) · [Graphical test guide](evidence/client-approval/graphical-test-guide.md)

### Connected browser follow-up

- A real API `unknown_tags` 422 preserved the edited document draft. After correcting the tag, retry saved the draft. Planned, In progress and Done each matched the API count and the rendered project totals. [Browser run](evidence/connected-browser/browser-results.txt)
- The pairing field and native selectors tested on Tickets, Activity and document import showed a visible inset focus indicator. The selectors reserved 34 CSS pixels on the right for a 16-pixel arrow placed 10 pixels inside the control border. The Tickets list fit at 1600, 1280 and 900 pixels. At 200% Chrome zoom, the Documents tag filter opened with Enter and its 16 × 16 CSS pixel checkbox toggled with Space. The pairing and checkbox fixes are tracked in [T-026](tickets/T-026-keep-keyboard-focus-inside-controls.md). [Pairing focus](evidence/connected-browser/pairing-focus.json) · [Tag filter at 200%](evidence/connected-browser/document-tag-focus-200.png)
- Final TypeScript, production build and all 14 mock browser checks passed. The independent reviewer inspected the focus CSS, browser assertions, saved results and the zoom screenshot. The reviewer confirmed the validation and progress evidence, and found no applicable findings in the zero-finding legacy scan. Connected visual evidence covers the exercised controls and layouts. [Check summary](evidence/connected-browser/check-summary.json) · [Legacy scan](evidence/connected-browser/legacy-scan.json)

### Client approval regression and repair

Unattended Claude Code applied an update on a synthetic project at revision 1 and returned revision 2 without human input. Source review also found that returning an MCP approval form could fall through to applying the change. The before-and-after Claude test did not trace which wire path it took. The repaired server grants interactive approval only to a dedicated verified credential and requires an explicit decision. The multi-step path also requires signed continuation state for the same pending request. [T-027 repair](tickets/T-027-require-verified-client-approval.md)

- After rebuilding, Claude Code 2.1.327 in the same unattended mode received `approval_required`, `applied: false` and a request ID. A follow-up read returned the same project at revision 1 with its original values. [Claude Code retest](evidence/client-approval/claude-code-result.md)
- A disposable API instance with a synthetic verified credential returned a form without applying, denied missing or mismatched state, retried a bound approval without a duplicate update, and preserved state after decline, cancellation or stale approval. Two accepts arriving at the same time applied a single change. Default Delete stayed pending. A ticket with two pending requests kept the separate **Needs approval** badge until both were resolved. The legacy SDK callback supplied an explicit accept that applied once. All three backend approval regressions passed. [MCP wire run](evidence/client-approval/wire-results.txt) · [Backend test output](evidence/client-approval/backend-tests.txt)

## Full Vision-to-stories and release evidence trace

This is a source and evidence audit; no runtime actions were performed. The paths in the runtime table above are recorded as run-owner results, not reproduced by this reviewer. No raw Compose, browser, REST or MCP run logs are linked from that table. The saved screen-review evidence predates the connected tag/upload states and explicitly limits its visual approval to the earlier mock scope.

### Vision feature coverage

All five Vision feature names appear in the active story index, and the story `Associated Features` use those names. No active story is unassociated with the Vision.

| Vision feature | Stories | Architecture and design coverage | Release evidence disposition |
| --- | --- | --- | --- |
| Product project management | US-001, US-002, US-011, US-012 | Projects/data/API/MCP; navigation and project screens | Project creation is in the browser run summary; project isolation appears in REST coverage. Project switching, same-name distinction, and edit preservation are still open. The expanded browser run records create-draft recovery. |
| Agent role management | US-003, US-005, US-011, US-012, US-013 | Roles/data/API/MCP/approval; roles and ticket ownership design | Role creation and an assigned ticket are in the browser run summary. Role-edit preservation and foreign-project role rejection are not specifically recorded. |
| Task coordination | US-004–US-008, US-010–US-013, US-016 | Ticket/link/tag API, MCP and approval; tables/boards and artifact operations | Atomic assigned-and-blocked create and document link are in the browser run summary; REST tag filters are reported. Full ticket transitions, link edge cases, and all tag-filter UI/REST/MCP parity cases are not recorded. |
| Document management | US-007, US-008, US-011, US-012, US-015–US-017 | Document API, upload provenance, revisions and approval; document history and artifact operations | Exact tagged Markdown upload, reload, edit/restore and ticket link are in the browser run summary; REST version and upload checks are reported. Compare, expired revision, malformed/unsupported upload and failure recovery are not all evidenced. |
| Progress tracking | US-006, US-009–US-010, US-012–US-014 | Progress/activity API, SSE, retention and maintenance; progress/activity/approval design | Progress and activity API checks, live approval badge and delayed live activity are reported. Full status history, 30-day boundary cleanup, stopped-service recovery and activity filter/dedupe criteria remain unverified in the saved summary. |

### Story-by-story evidence matrix

“Recorded” means the current Local runtime evidence table names the path; it does not imply this reviewer independently reproduced it. “Not recorded” means no corresponding result is stated in the saved evidence summary, even where source support exists.

| Story | Feature trace | Recorded release evidence | Not recorded or still open |
| --- | --- | --- | --- |
| US-001 Create project | Product project management | Browser project creation; REST repeat-create keys | Purpose after reload, blank-name rejection and edit preservation. Save-failure recovery was exercised in the expanded browser run. |
| US-002 Find/switch projects | Product project management | REST project-scoped ownership/read coverage | Same-name disambiguation and empty state. The expanded run selected the persisted project after restart and verified cross-project REST isolation. |
| US-003 Define roles | Agent role management | Browser role creation | Missing-field recovery, editing an assigned role without losing assignment, and no-launch representation. |
| US-004 Create/prioritize tasks | Task coordination | One-request assigned/blocked ticket creation | Blank-title recovery, priority ordering and edits preserving owner/status/links. |
| US-005 Assign responsibility | Agent role management; Task coordination | Assigned ticket creation; project-scoped ownership in REST smoke | Self/role reassignment preservation, unassigned labeling and rejection of a foreign-project role. |
| US-006 Track status/blockers | Task coordination; Progress tracking | Blocked ticket created with blocker explanation | Planned/In Progress/Done transitions, clearing/reopening blockers, and failed-save retry behavior. |
| US-007 Maintain documents | Document management | Upload, reload, edit and restore browser path; REST revision-count check | Manual create/empty-content validation, old-content history comparison and failed-save draft recovery. |
| US-008 Link documents | Document management; Task coordination | Browser link from the ticket inspector; REST link coverage | Duplicate-link idempotence, cross-project target rejection, unlink preservation and return navigation. |
| US-009 Review progress | Progress tracking | REST project progress check | Browser count-to-task navigation, blocker owner display, empty state and unavailable-data retry. |
| US-010 Review task changes | Progress tracking; Task coordination | Activity API and live event paths are reported | Previous/new status or owner values, ordered history after reopening, and no success event on failed update. |
| US-011 MCP operations | Product project, role, task and document management | Both standalone terminal clients exercised create/read, document history, activity and reconnect. Python SDK discovery exposed 31 tools, including over the Claude Desktop stdio bridge. | Native graphical client workflows and full AgentBuild command reuse. |
| US-012 Client approval | Task, progress, document, role and project management | Codex CLI and Claude Code terminal accept, decline and stale checks passed. The SDK verified replay and concurrent accept. With two pending requests, the badge stayed visible until both were resolved, independently of task status. | Native graphical approval workflows and unsupported behavior by client. |
| US-013 Report/review activity | Progress tracking; Task coordination; Agent role management | Delayed activity appeared live; REST/MCP activity paths reported | Each filter, duplicate delivery, failure attribution and task-history reconstruction are not individually evidenced. |
| US-014 Expire activity | Progress tracking | Maintenance service startup and source implementation; retention query path in REST smoke | The expanded REST check proved old receipts were excluded and expired cursors caused resync. On a disposable Postgres database migrated from empty, maintenance physically deleted overdue and exactly 30-day receipts and retained one receipt a microsecond newer. A long-running scheduler outage was not exercised. |
| US-015 Document revisions | Document management | Browser edit/restore/reload; REST current-plus-three revision check | Diff comparison, unavailable pruned revision, failed/unapproved update history, and native MCP revision/restore workflows. |
| US-016 Filter by tags | Document management; Task coordination | REST tag filters and MCP catalog validation were exercised. Metadata-only MCP listing preserved tag filtering, project scope, cursor pagination, and empty pages. The executed Postgres query selected individual metadata fields and excluded both the body and original frontmatter. A full read in the same session still returned both exactly. For the three-document fixture the summary returned 1,846 JSON bytes versus 37,306 for full records. [Summary examples](technical-architecture/contracts/mcp/README.md) | Full REST/MCP pagination parity matrix. Browser keyboard tag selection was exercised at 200% zoom. |
| US-017 Upload metadata | Document management | Browser reviewed a tagged Markdown file with BOM/CRLF frontmatter, saved and reopened it; exact frontmatter/content preservation is recorded | Unsupported format, malformed/unknown-field correction, request-size boundary and network-failure retry are not separately recorded. Source now stores original frontmatter and blocks over-limit serialized payloads. |

### Client and release gate matrix

The architecture client gate requires actual discovery, Create/Read, approval accept/decline/unsupported/stale, restart/reconnect, duplicate calls, revision reads and activity append for each named configuration (`technical-architecture/mcp-tools.md`; ticket T-010). Current recorded status:

| Client/path | Evidence currently recorded | Gate status |
| --- | --- | --- |
| Python MCP SDK over authenticated HTTP | Tool discovery, auth rejection, read/create, pending without elicitation, accept, decline, replay and terminal payload clearing | SDK behavior exercised; not a substitute for each native client. |
| Claude Desktop stdio via SDK callback | The documented Docker command discovered 31 tools under a minimal process search path when called by absolute path. A migrated disposable database verified setup and role reuse, tagged planning records, ticket replay and context linking, pending and approved edits, rejected deletion, revision reads and activity. [Bridge and connected records](evidence/client-approval/connected-stdio-workflow.md) | The graphical app's approval UI remains unverified. |
| Codex app-server | 31 tools, Create/Read, actual elicitation requests answered by the harness, accept/decline/stale, post-reconnect read, duplicate document Create, revision list, and activity append | Installed app-server exercised; native GUI interaction remains unverified. |
| Codex CLI | Standalone `codex exec` verified same-key project creation, document and revision reads, activity append/list, and a fresh process reconnect. The terminal UI displayed a separate approval form and passed accept, decline, and stale revision checks with scripted keypresses. Both runs used a deterministic localhost model mock. [Standalone and reconnect](evidence/client-approval/codex-exec-reconnect.txt) · [Terminal approval](evidence/client-approval/codex-terminal-approval.md) | Terminal approval verified for the tested configuration. |
| Claude Code | 31 tools discovered. Installed CLI exercised project Create, duplicate Create, Read, document creation and revision reads, activity append/list and fresh reconnect. Default unattended Update stayed pending. The terminal UI passed accept, decline, and stale revision checks with scripted keypresses. [Standalone and reconnect](evidence/client-approval/claude-code-final-workflow.md) · [Terminal approval](evidence/client-approval/claude-code-terminal-approval.md) | Terminal approval verified for the tested configuration. |
| Local browser + REST/Compose | Pairing, project/role, tagged upload, edit/restore, atomic assigned/blocked ticket, link, approval badge, activity, readiness | Expanded connected flow, real Chrome page zoom, keyboard, draft recovery, restart persistence, isolation and expired cursor resync recorded above. |
| Mock frontend regression | TypeScript, production bundle and 14 mock browser checks | Recorded pass, but mock checks do not establish connected backend behavior. |
| Backup/recovery | Archive creation and temporary-database restore are reported; archive files are present in `.local/backups` | Reported pass; restore transcript is not attached. |

The run owner completed the expanded Chrome and API checks recorded above. The source reviewer did not independently execute them. Activity filtering and resync were tested against aged fixtures. The maintenance cleanup function physically deleted aged records on a fresh disposable database at the 30-day boundary. A long-running scheduler outage and measured notification latency remain separate checks.
