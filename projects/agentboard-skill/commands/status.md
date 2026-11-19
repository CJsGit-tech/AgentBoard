# Contract: Status <ProjectName>

## Purpose
Report verified progress, artifact versions, local/remote storage and next actionable command, without generating product documents.

## Preconditions
Identifiable AgentBoard project, or an explicitly selected local-only project. Status reads the canonical target and never creates one.

## Owner
Orchestrator.

## Required context
Read `references/document-folders.md` first. For folder-layout projects, inspect the relevant README and open only selected story/topic files; do not assume old combined document paths.

AgentBoard project records and `references/agentboard-integration.md`, or a local `project-manifest.json`, actual docs, ticket index and agent charters for an explicitly selected local-only project. `references/local-workspace.md`.

## Execution
1. Resolve the previously established AgentBoard project by its verified ID or unique name; otherwise resolve the explicitly selected local-only project. Use the verified MCP connection to the manually started Compose app; report if it is unreachable.
2. Read project records and actual app state, or the local manifest/files in local-only mode. Report actual documents, state/version, roles, open decisions and change impacts. Do not claim subagents are running merely because role records/files exist.
3. Show the storage target as AgentBoard app or local-only files, and report app record IDs or file paths. A locally hosted AgentBoard app is still app mode; do not equate the manifest's `local_only` state with pending sync.
4. Identify missing prerequisites, stale downstream documents, approval/revision needs and any local/remote discrepancy.
5. If tickets exist, report FE/BE and BUG/BUILD counts, blocked work and reported-versus-confirmed bugs; a role file does not mean an agent is running. Keep ticket status separate from document lifecycle and Needs approval.
6. Suggest earliest valid next command; do not create new documents during Status.

## Output artifacts
Concise status reply (no file required).

## Acceptance checks
- State grounded in manifest **and actual files**; no inferred human approval.
- Local-only mode is represented as legitimate, not blocked.
- Next recommendation respects dependencies.

## Persistence updates
Read-only; no local or remote mutations.

## Failure handling
If no local/verified remote project exists, recommend `Setup <ProjectName>` and explain that missing AgentBoard will trigger a one-time local-storage confirmation before any writes.
