# Contract: Setup <ProjectName>

## Purpose
Create or reuse an AgentBuild project with six default role definitions. **Never silently replace unavailable AgentBoard storage with local storage.** Obtain explicit consent first.

## Preconditions
- An identifiable project name.
- Verified authorized AgentBoard operations **or** an already confirmed local project **or** explicit user consent to local fallback.
- Writable workspace if local storage is selected.

## Owner
Orchestrator. Default role charters are in `roles/*.md`.

## Required context
Project name, actual workspace/root, existing local manifest if any, verified AgentBoard integration (if available), `references/local-workspace.md`, `references/agentboard-integration.md` and project manifest template.

## Execution
1. **Read-only discovery.** Resolve project name, candidate local path, existing local consent and real AgentBoard capabilities. Do not write files or create remote records while deciding fallback.
2. Use the verified MCP connection to the manually started Compose app. If the installed app is stopped, report that it must be started using its documented Compose instructions.
3. If AgentBoard project/agent creation is available and authorized, create/reuse the app project and missing role records idempotently. Don't claim agent-spawning capability without verification.
4. If AgentBoard is not installed and the user has not chosen a target, ask whether to use file-only mode or cancel/install AgentBoard. If a previously confirmed file-only project is being continued, reuse it. If the installed app cannot start or lacks the operation, report that blocker and stop; do not redirect to files automatically.

   > AgentBoard is not installed. Choose a storage target for **<ProjectName>**: **Use file-only mode** at **<resolved-path>**, or **Cancel** and install/connect AgentBoard first. File-only records will not be part of an AgentBoard workspace.

5. **Do not write until a target is selected.** File-only projects require recorded consent, an explicit current file-only choice, or an affirmative answer to the prompt. Cancel means **no local files and no app records changed**. Do not infer permission from the initial Setup request.
6. On `Yes`, execute `python3 <skill-root>/scripts/scaffold_project.py --name "<ProjectName>" --user-approved-local` with `--root` only for an established alternative projects root. Pass the project name as one argv value; never interpolate it into shell text. Explicit command option `--local` from the user also counts as prior consent.
7. The scaffold creates/reuses `project-manifest.json`, empty `docs/` and `agents/*.md` for Product Manager, Product Designer, Solution Architect, Backend Programmer, Frontend Programmer, and Code Reviewer. Preserve existing edits; do not create blank product documents.
8. Validate project structure. Report target, created/reused role records or local charters, and next command `Vision-Document <ProjectName>`. Local role files are not running subagents.

## Output artifacts
- After local consent: `<workspace>/projects/<slug>/project-manifest.json`, `agents/*.md`, `docs/`.
- With verified remote access: confirmed project and role records.
- Before consent: only the Yes/No question; **no file outputs**.

## Acceptance checks
- No local project is created without first-time consent.
- A repeat Setup uses recorded per-project consent without re-prompting and preserves customized files.
- User refusal leaves project path uncreated/unchanged.
- No invented remote IDs or running-agent claims.
- Local manifest records `local_storage_confirmed: true`, `storage_mode: local`, `sync_state: local_only`.

## Persistence updates
Only after approval: local manifest and role charters. Only after verified remote authorization: supported AgentBoard records. Never silently synchronize local output.

## Failure handling
If AgentBoard is not installed, ask the user to choose file-only mode or cancel/install the app. If an installed app cannot start or become ready, report the blocker and stop. If the user cancels the storage choice, report cancellation. If the file system is unavailable **after file-only mode is chosen**, report the blocker; do not claim setup succeeded.
