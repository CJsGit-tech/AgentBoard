# Architecture document plan, profiles, skeletons and quality gates

## Workflow

1. Inspect Vision, the User Stories README and relevant individual stories. Establish whether the app is web, iOS, or both.
2. Complete multi-round discovery: deployment, access/users, stack preferences and alternatives, providers, integrations, data, security/privacy, scale, offline/realtime/background behavior, and operation/release needs. Reuse already confirmed answers.
3. Propose a concrete document plan: shared documents, platform profile(s), each optional topic's trigger and whether it needs a file or an inline section, and explicit reasons for non-applicability. Link selected optional concerns to actual US IDs or named stakeholder decisions. Confirm this document plan alongside the discovery brief, or use explicit user delegation already given. Do not ask again if it is already confirmed.
4. Run the skeleton script only after plan confirmation and local project storage consent. Skeleton creation is not architecture generation or completion.
5. Fill documents using the catalog contracts and actual requirements. Replace every scaffold marker/WRITE placeholder, explain N/A with a reason, verify changing technical claims using official sources, and create a real module-oriented SVG.
6. Map every story acceptance criterion to one or more selected documents in the plan. Review semantics: the referenced content must actually support the criterion, not merely contain its ID.
7. Run automated validation; then review coverage, cross-document consistency, diagram agreement, and technical evidence. Resolve critical/blocking findings. Record concrete review notes and remaining nonblocking findings in the plan. A review note is a record of work, not proof supplied by the script.
8. Run project validation again, update artifact/version metadata deliberately, and report drafts, validation results, assumptions, and unresolved issues. Never call skeletons completed documents or automatically approve drafts.

## Fixed shared documents

```text
technical-architecture/
  README.md                    # Short overview, diagram, navigation, assumptions
  system-architecture.svg
  document-plan.json           # Confirmed selection, discovery, coverage, review record
  technology-stack.md
  data-model.md
  api-integrations.md
  security-privacy.md
  testing-strategy.md
  decisions.md
```

For web add `web/frontend.md`, `web/backend.md`, `web/deployment.md`.
For iOS add `ios/app-structure.md`, `ios/platform-capabilities.md`, `ios/release.md`.
For both generate both profiles and keep shared rules in shared documents. Do not duplicate backend/API/data policy in client files. Core concerns still need coverage when not applicable; write N/A with a specific reason, not an empty document.

`assets/architecture-documents.json` is the authoritative topic/heading/prompt catalog. Each document has a contract, not merely a filename. Example approval contract: actions/approvers; request states including rejection/cancel/timeout; exact change/revision binding and stale approval; enforcement across UI/API/data and unsupported clients. An approval heading alone does not satisfy this contract.

## Optional topics and triggers

| Topic | Trigger |
| --- | --- |
| authentication | Login, access roles or account recovery |
| payments | Purchases, subscriptions, refunds or payouts |
| offline-sync | Offline edits synchronize later |
| background-jobs | Scheduled/retriable/cancellable work outlives requests or foreground sessions |
| realtime | Live updates, subscriptions or event streaming |
| file-storage | Upload storage/access/processing/retention |
| mcp-tools | AI clients operate the app through MCP |
| approval-flow | Human approval or staged authorization |
| document-history | Versions, comparison or restoration |
| activity-logging | User-facing activity feed or audit trail |

Inspect requirements for these triggers and ask about unknowns; no keyword heuristic proves a requirement. Every optional topic must have an explicit decision:

- `file`: standalone workflow, rules, failure cases or contracts justify `<topic>.md`.
- `section`: small concern fits a named heading inside another selected document. Specify `covered_in: {"path": "security-privacy.md", "heading": "Local Authentication"}`. The heading is added to that document's contract; it is not silently omitted.
- `not-applicable`: explicit product-specific reason; do not create a file. Leave requirement references empty when there is no triggering requirement.

New product concerns outside this catalog should be raised during discovery and added to the catalog with a reviewed contract before scaffolding; do not improvise an unvalidated filename silently. Revisit document selection when requirements change. Preserve prior authored files and request confirmation of changed choices rather than overwriting the old plan or removing files.

## CLI and plan fields

The script prints proposed JSON without touching project files:

```sh
python3 <skill-root>/scripts/architecture_documents.py plan --profiles web
python3 <skill-root>/scripts/architecture_documents.py plan --profiles ios
python3 <skill-root>/scripts/architecture_documents.py plan --profiles web ios
```

Save a working copy where appropriate; fill discovery `context`, optional decisions and their requirement references. Do not set `status: confirmed` until the human has confirmed the document list/brief or explicitly delegated those decisions. The file is an assertion of confirmed decisions, not a substitute for obtaining them.

After confirmation:

```sh
python3 <skill-root>/scripts/architecture_documents.py scaffold --project <project-path> --plan <confirmed-plan.json>
```

This creates only selected Markdown skeletons, navigation, `document-plan.json` and an unmistakably unfinished SVG. It creates missing files only, preserves every existing file, reports existing README link conflicts, and rejects a differing saved plan. It does not write product content or change project manifest artifact states. On reruns, use the current saved plan. To change selection, explicitly revise/archive the plan first and pass that same updated plan; manually add navigation links if README already exists. Obsolete documents are never deleted automatically. No snapshots, generated exports, database or custom storage engine is introduced.

For existing projects without document-plan.json, prior folder validation remains supported. Do not migrate AgentBoard or rewrite its current architecture merely because this skill is updated. On a later authorized architecture revision, propose how existing files map to the fixed topics, preserve their content/history, and then adopt the plan.

## Authoring and validation

Every generated heading has a prompt describing the actual answer needed. The final content must be project-specific, readable and consistent with stories. Remove the skeleton marker only after authoring; deleting it without filling sections still fails empty/placeholder checks. Metadata includes Owner, Version, Status, Last Updated. Story documents retain their separately agreed three-field format.

`coverage` maps actual criterion numbers to document paths. Example:

```json
{"US-012": {"1": ["approval-flow.md", "mcp-tools.md"], "2": ["web/frontend.md"]}}
```

Include every criterion of every current story; numbers are their order within Acceptance Criteria. Unknown story IDs, nonexistent criterion numbers and unselected paths are rejected. A stable story ID is preserved; when criteria change, review and update the mappings. References to named non-story decisions remain plain explanatory references. The script checks existence/completeness of the map; reviewers assess whether the linked design satisfies the behavior.

Record `review.status: reviewed` only after performing the review. Fill the review fields `story_coverage`, `consistency`, `diagram`, and `evidence` with concrete findings/checked relationships and sources. `findings` is a list of objects with description, severity and status; unresolved critical/blocking findings prevent readiness. Nonblocking findings remain visible in the report. This is not human approval.

```sh
python3 <skill-root>/scripts/architecture_documents.py validate --project <project-path>
python3 <skill-root>/scripts/validate_project.py --project <project-path>
```

Checks: confirmed profiles/selection and rationale; required selected files/headings/content/metadata; incomplete markers; navigation; actual SVG vs placeholder; story criterion mappings; review record and blocking findings. Project validation also checks local links and original folder constraints. Tool output proves structural checks only. It does not verify runtime behavior, external compatibility, architectural correctness, or that a review actually happened. Inspect/render the diagram and assess the design separately before claiming quality.

## Contracts and JSON examples

Apply `contracts-and-examples.md`. Keep exact OpenAPI/domain/MCP schemas under technical-architecture/contracts/ and labeled examples under examples/. Skeleton contract scopes must be resolved and examples validated before reporting completion. Existing topic names remain supported; no automatic reorganization is required.

## Completion consistency

Follow output-consistency.md. Use sync_navigation.py for explicitly marked story/MCP navigation blocks and check_outputs.py --strict for one read-only gate. Derive indexes from canonical sources, declare important example outcomes/statuses, and keep semantic review separate.
