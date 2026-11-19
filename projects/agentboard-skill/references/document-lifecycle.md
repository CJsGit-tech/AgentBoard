# Document lifecycle, ownership, and traceability

## States

`not_started` → `draft` → `in_review` → `approved` → `superseded`.

`blocked` is an interruption state; retain the previous state and unresolved blockers in notes if supported. Never transition to `approved` automatically. A new revision of an approved artifact is a separate draft/version, not a silent overwrite.

## ID and linking policy

- `G-001` — preserve existing product goal IDs where present; the concise Vision does not require new goal IDs.
- `UC-001` — preserve existing use-case IDs where present; the concise Vision does not require new use-case IDs. Reference Vision feature names when IDs are absent.
- `US-001` — user stories, each linked to a `UC` or `G` where applicable.
- `T-001` — engineering tickets; one stable ID per file under `docs/tickets/`. Ticket workflow status is separate from document lifecycle and approval badges.
- `ADR-001` — architecture decision records (within Technical Documents).
- Cross-references should use IDs and a readable title, not fragile line numbers.
- Preserve IDs when editing wording. Mark deleted/split items as deprecated and record replacement links; never silently reuse old IDs for different meanings.

## Versioning

Use `major.minor.patch` strings for document revisions; start at `0.1.0` as a working draft where appropriate. Include `Owner`, `Status`, `Version`, and `Last Updated` near the top of project documents. Timestamp should be the actual execution date, never the template placeholder.

## Change-impact handling

On each requested revision:

1. Read current approved state, not just the last chat turn.
2. Summarize what changes and what remains unchanged.
3. Identify dependent artifacts (`vision → stories → architecture/design`).
4. Draft a revised document or diff for approval where required.
5. Flag affected artifacts as **needs review** in commentary/status or metadata; do not silently regenerate them.
6. Preserve prior version and stable AgentBoard reference if supported.

## Conflict precedence

1. Explicit current human decisions (unless restricted by higher-priority rules).
2. Latest approved project documents.
3. Draft project documents / referenced research.
4. Documented assumptions.

A conflict between two approved documents is a **decision to resolve**, not a reason to invent a new requirement.
