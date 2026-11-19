# Contract: Help

## Purpose
Describe AgentBuild commands, prerequisites, output paths, **opt-in** local fallback and safe revisions.

## Preconditions
None. Must work with no project, no AgentBoard and no filesystem writes.

## Owner
Orchestrator.

## Required context
`SKILL.md` command table and `references/local-workspace.md`.

## Execution
1. Show invocation `AgentBuild <Command> <ProjectName>`. Help needs no project name.
2. Explain all commands and which documents each produces.
3. Show recommended flow: Setup → Vision → Stories → Architecture and Design → Create-Screens (optional; all screens with mock data in the confirmed frontend stack) → Review, with Status anytime. Create-Tickets can turn available scope into BUILD work or accept simple BUG/improvement reports at any stage of an existing project; completed screens are not mandatory.
4. Explain the storage choice when AgentBoard is not installed: the user can select file-only mode at `<cwd>/projects/<slug>` or cancel and install/connect the app. The skill writes nothing until a target is selected. If an installed app fails, explain the issue and do not switch storage; file-only projects store role definitions in `agents/` and documents in `docs/`.
5. Explain that connected commands write directly to AgentBoard; local documents are an opt-in fallback. For Create-Screens, explain that a connected project also needs an existing local code checkout for source and verification evidence; this does not move planning records out of AgentBoard. Explain Create-Tickets: FE/BE ownership, BUG/BUILD work types, one ticket file per item only in local mode, day estimates with explicit scope, and reported bugs investigated without invented reproduction steps.
6. Explain that existing artifacts are preserved, revisions archive previous versions, and local mode does not queue remote sync.

For an existing project, show `AgentBuild Update <ProjectName> --preview` to trace changes across documents, stories, and tickets, and `AgentBuild Update <ProjectName> --apply <plan-id>` to apply a reviewed plan under the normal storage and approval rules. Omitted mode defaults to preview.

## Output artifacts
Conversation response only.

## Acceptance checks
- Lists all commands and dependencies.
- Explicitly states AgentBoard is the normal target when installed; Setup must obtain user approval before first-time local fallback.
- No claims of installed/running agents without evidence.

## Persistence updates
None.

## Failure handling
If command is unknown, state it is unsupported and list supported commands; do not invent functionality.
