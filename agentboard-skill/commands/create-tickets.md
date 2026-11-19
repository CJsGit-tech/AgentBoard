# Contract: Create-Tickets <ProjectName>

## Purpose
Turn product scope or simple user feedback into actionable, linked engineering tickets. Role is FE or BE; type is BUG or BUILD. Create tickets, not implementation or automatic document rewrites.

## Preconditions
An identifiable existing AgentBoard project or confirmed local project. A simple report is enough for intake; users need not supply technical causes, logs or reproduction steps. Planning a backlog needs relevant product scope, but does not require completed screens. Use AgentBoard directly when connected; never silently switch to local storage or create a project.

## Owner
Product Manager coordinates intake and decomposition. FE maps to `agents/frontend-programmer.md`; BE maps to `agents/backend-programmer.md` (fall back to skill role charters if absent). The role field routes future work; it does not claim an agent has run.

## Required context
Read `references/tickets.md`, `references/artifact-metadata.md`, `assets/templates/ticket.md`, the project manifest and ticket index first. Open only relevant stories, architecture/contracts, approved screens and source. For simple feedback, preserve the user's report and use available context without requiring unrelated planning documents.

Use the existing `docs/tag-vocabulary.json`; if missing, derive feature IDs from Product Vision before creating tickets. Never invent feature labels or use role/type/status/milestone values as tags.

## Execution
1. Determine whether the user requests backlog planning, a problem report or an improvement. Preserve report wording with source attribution. BUG means reported or evidenced incorrect behavior; BUILD covers new capabilities, improvements and agreed behavior changes. No UPDATE ticket type. Distinguish intent from uncertain diagnosis; ask only if that ambiguity materially changes scope.
2. Inspect existing tickets and implementation before adding work. Reuse a matching ticket; never duplicate reported symptoms solely because wording differs. Keep IDs stable and allocate the next unused `T-###`; never renumber or reuse retired IDs.
3. Assign exactly one FE or BE role per ticket. When the cause is unknown, mark assignment provisional and explain the initial investigation owner. Prefer the role closest to available evidence; do not infer BE merely from a save failure. Split cross-stack outcomes into linked FE and BE tickets with explicit shared contracts and dependencies; avoid creating a ticket per file/component.
4. For BUG intake, use `Verification: Reported` unless real existing evidence supports another state. Copy only supplied or actually observed steps, labeling their source and whether independently tested. Unknown reproduction is valid. The assigned programmer investigates during authorized execution, records attempted checks and actual results, and updates verification with evidence. Do not run unrequested implementation or manufacture reproduction steps, a root cause, a successful reproduction or a failing test to fill fields. Report missing access as blocked investigation; failure to reproduce does not prove no bug exists.
5. State the outcome and acceptance criteria. For unverified BUGs, separate investigation criteria from conditional repair criteria: establish expected behavior, investigate, fix if confirmed, and provide regression evidence if repaired. Do not promise a particular repair before diagnosis. BUILD criteria express agreed outcomes; identify proposals rather than presenting inferred requirements as approved.
6. Add Estimate (days), Estimate scope and Estimate basis to every ticket using `references/tickets.md`. Include estimates/scopes in the index. Estimate effort in decimal days; use bounded investigation estimates for unverified BUGs and disclose that repair is not yet estimated. Never imply effort is a delivery date.
7. In connected mode, create or update AgentBoard ticket records directly through verified MCP operations, storing tags, FE/BE role, BUG/BUILD type, estimate and ticket details as structured fields; verify returned record IDs. In local fallback mode, write one `docs/tickets/T-###-short-title.md` per ticket with the required YAML header and maintain the filterable README. Keep task-relevant context links; do not copy whole specifications. Use the app's approval flow for agent updates/deletes. All tickets use required fields and sections from the reference.
8. Preserve history before authorized revisions. Creating/read access does not imply approval to update/delete existing app records. Follow project approval policy; when updating a matching ticket requires approval, propose the concrete edit and keep Needs approval separate from status. Do not create a duplicate to bypass approval. Do not rewrite requirements to fit code or automatically close tickets.
9. Run `python3 <skill-root>/scripts/check_tickets.py --project <project>` and `check_outputs.py --project <project> --strict`. Review scope, duplicates, role routing, truthful evidence and actionable criteria separately; scripts cannot verify factual reports or diagnosis. Fix structural errors before reporting valid output.

## Output artifacts
AgentBoard ticket records when connected, or `docs/tickets/README.md` plus individual ticket files in local fallback mode. No tickets are generated merely by installing/updating this skill.

## Acceptance checks
- Each ticket has one FE/BE role and one BUG/BUILD type; provisional ownership is explicit when appropriate.
- Each ticket has a positive day estimate, scope and basis; uncertain BUG repairs are not invented or counted as zero.
- Simple user feedback is accepted without asking the user to diagnose or reproduce it.
- Reported versus agent-observed facts are distinguishable; no invented reproduction or verification claims.
- Stable unique IDs, one file per ticket, working index/context links and valid acyclic dependencies.
- Existing implementation and tickets considered; no duplicated work or unsupported approval/completion claims.
- Structural checks pass and semantic coverage/evidence reviewed; missing facts remain explicit.

## Persistence updates
Write directly to the verified AgentBoard project when connected. In local mode, register `artifacts.tickets` at `docs/tickets/README.md`, layout `folder`, owner `product-manager`, state `draft`, actual version/timestamp and relevant existing artifact dependencies. Match collection metadata in README; individual ticket status remains separate. Do not add empty tickets to Setup. Preserve the selected storage mode.

## Failure handling
Missing reproduction is not a blocker to creating a reported BUG. Record unknowns and let the assigned role investigate. Ask only for information needed to proceed that available context cannot provide. Missing evidence blocks confirmed/fixed claims, not intake. Missing project/storage authorization follows the shared consent rules.
