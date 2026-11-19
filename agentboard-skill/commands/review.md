# Contract: Review <ProjectName>

## Purpose
Review planning documents for coherence, completeness, traceability and feasibility. Produce a prioritized review report without silently rewriting source documents.

## Preconditions
At least one actual planning artifact exists locally or as a verified remote document. Full cross-document review needs Vision, Stories, Architecture and Design.

## Owner
Code Reviewer — local `agents/code-reviewer.md` if present; otherwise bundled charter. Label same-session review as self-review if no independent runtime agent was invoked.

## Required context
Read `references/document-folders.md` first. For folder-layout projects, inspect the relevant README and open only selected story/topic files; do not assume old combined document paths.

Read real current records from the canonical AgentBoard project, or files from an explicitly selected local-only project; inspect approved decisions, status/version, `references/quality-gates.md`, and `assets/templates/review-report.md`.

When Review includes frontend source checks or screen evidence, use an existing code checkout as an implementation/evidence workspace. In connected mode, keep planning records and the review report in AgentBoard; the checkout does not switch the project to file-only mode. Do not create a local project copy automatically. See `references/agentboard-integration.md#local-implementation-and-evidence`.

## Execution
1. Resolve the canonical AgentBoard project or approved local-only project and gather only artifacts that actually exist. Use the verified MCP connection to the manually started Compose app. Do not initialize a project without verified app capability or explicit local consent.
2. Run the applicable structural/contract checks for the selected target and separate semantic evaluation. Passing structural checks does not equal correctness.
3. Trace Product Vision feature names to `US-###`, then technical/design specifications. Preserve and check `G-###`/`UC-###` links only where those legacy IDs actually exist; their absence is not a defect in a current concise Vision. Check error/empty/permission behaviors, API/security/privacy/accessibility and implementation assumptions.
4. For each finding use stable `R-###`, severity, affected file/version, evidence, remediation and owner; distinguish observations from suggestions.
5. Verdict is `blocked`, `changes_requested` or `reviewed_with_no_blockers`, never auto-approved. State missing artifacts explicitly for partial review.
6. Write a completed report to the canonical AgentBoard project through verified document operations, or save to `docs/review-report.md` with `scripts/save_artifact.py --artifact review` in local-only mode. Preserve prior review history.
7. Validate, then report the actual AgentBoard project/record IDs or local paths and remaining issues. Never describe an unverified local or app write as persisted.

## Output artifacts
Review report record in AgentBoard, or `docs/review-report.md` in local-only mode.

## Acceptance checks
- Follow references/output-consistency.md: synchronize marked navigation, then run check_outputs.py --project <project> --strict. Preserve human text; fix source/schema/example drift before reporting consistency.
- Findings anchored in specific existing content and versions; omissions explicitly stated.
- No unapproved source-doc changes, fabricated defects, or automatic approvals.
- Review report saved in the selected canonical target and verified.

## Persistence updates
In AgentBoard mode, write the report as a document record and verify its ID. In local-only mode, update the manifest `review` entry with version/draft state.

## Failure handling
If no documents exist, explain and suggest Vision-Document. If AgentBoard cannot start or connect, review existing local files only when this project is already explicitly local; otherwise ask before switching to local files. Saving locally requires prior local approval.
