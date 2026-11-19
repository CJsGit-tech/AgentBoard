# Ticket format and investigation

## Layout and navigation

```text
docs/tickets/
  README.md
  T-001-create-project-api.md
  T-002-connect-project-form.md
```

Use ordinary Markdown, one ticket per file. README contains collection Owner/Version/Status/Last Updated metadata and an ID/title, Role, Type, Status, Verification, Estimate (days), Estimate scope, Link table. Read it first, then only task-relevant tickets/context. Add `artifacts.tickets` only when tickets are actually created; leave unrelated document formats intact.

Each index and ticket also starts with the required YAML metadata header in `artifact-metadata.md`. Ticket feature tags should match the work's real Product Vision area; optional concern tags support cross-cutting searches. Never use tags for role, type, milestone, status, or estimate.

## Required ticket fields

Use a title `# T-001 — Short actionable title` and one plain metadata line per field:

- Role: FE or BE. These map to the project Frontend Programmer or Backend Programmer charter.
- Type: BUG or BUILD. Improvements and agreed requirement changes are BUILD.
- Status: Open, In progress, Blocked, Done or Cancelled.
- Verification: BUG uses Reported, Investigating, Confirmed, Not reproduced, Fixed or Not a bug. BUILD uses Not applicable.
- Assignment: Confirmed or Provisional. Provisional indicates a starting investigation owner, not a diagnosed cause.
- Estimate (days): a positive decimal effort estimate, such as 0.5 or 2.
- Estimate scope: Build, Investigation or Repair. BUILD uses Build; BUG uses Investigation or Repair.
- Estimate basis: brief scope, assumptions and uncertainty; include implementation, relevant tests and review where applicable.
- Depends on: None or comma-separated stable ticket IDs. Related tickets use links in Context; not every relation is a dependency.

Keep Needs approval as an independent badge/field when the project needs it, never a ticket status. README document status is the collection lifecycle; it does not mean all tickets are open, approved or complete.

Required sections: Outcome, Acceptance Criteria, Context. BUG also requires User Report, preserving informal feedback with provenance; test-discovered bugs cite the actual test/run instead. Use Investigation and Completion Evidence when work produces results. Keep known unknowns explicit; do not leave copied template placeholders in output.

Context links only relevant story files, architecture topics, operation schemas, screens, existing source or related tickets. Bare external URLs are not local verification evidence. If no document covers a report, say so rather than fabricating a link or requirement.

## Estimates and timelines

Every ticket has an estimate in days, including reported BUGs. Default planning convention: one day is eight focused working hours for one assigned worker; use a confirmed project convention if different and record it in the ticket index. This is estimated effort, not a promise of agent runtime or elapsed calendar duration. Decimal days are allowed.

For BUILD, estimate the scoped implementation, tests and review. For an undiagnosed BUG, estimate a bounded investigation first, label scope Investigation and explicitly exclude unknown repair effort. Once evidence establishes the repair, revise the estimate/scope with authorization and a brief reason; do not disguise investigation as a full repair estimate. If uncertainty is high, label the estimate provisional and explain the assumptions; missing diagnosis must not become false precision.

Show estimates and scopes in the ticket index so AgentBoard can use them for planning. Preserve original estimates when recording revisions. Dependencies, capacity, parallel work and approval waits affect calendar forecasts; do not invent start/due dates or compute a delivery date by simply adding FE/BE effort. Unknown repair effort is excluded from totals, not zero. Do not introduce timeline UI, contract or schema changes while merely generating tickets.

## BUG evidence

Accept reports such as “saving loses my input.” Initial reproduction and cause may be unknown. Record supplied steps as user-reported, not agent-tested. Label actual agent observations with the method and result; separate hypotheses from findings. Do not infer a source of failure from the visible symptom.

During authorized ticket execution, the assigned role investigates with available source/tests/runtime, keeping a concise record of attempted checks and results. Questions should resolve genuine blockers, not demand technical diagnosis from the user. Reassign or split FE/BE when evidence supports it, preserving the original report and links.

Confirmed requires actual supporting evidence. Not reproduced means the listed attempts did not reproduce it, not that the report is false. Not a bug requires evidence of intended behavior and an explanation; a desired behavior change may become a linked BUILD proposal. Fixed requires repair verification and a regression check where appropriate. Never invent steps, logs or test results to meet a template.

## Completion and repeat runs

Done requires linked, reviewable completion evidence. For a BUG, resolution must be Fixed or evidence-backed Not a bug; otherwise leave investigation open/blocked or explicitly cancel it with a reason. An independent reviewer verifies closure when project policy requires one. Ticket creation alone does not dispatch or complete implementation.

Repeated runs inspect IDs, outcomes and report evidence before allocation. In connected mode, create records directly in AgentBoard and preserve returned IDs; in local mode, maintain the authorized local files. Preserve existing status, completion and user edits; add evidence to matching tickets only when updates are authorized. There is no separate Sync command or background file watcher: connected planning commands write to the app directly, while local-only projects remain independent.

`check_tickets.py` is read-only: it checks shape, identity, role/type enums, index coverage, local links, dependencies and obvious unsupported Done states. It cannot establish whether reports, reproduction or evidence are true; review those separately.
