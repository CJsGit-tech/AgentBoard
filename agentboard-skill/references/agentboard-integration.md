# AgentBoard integration — preferred canonical workspace

AgentBoard is the normal project workspace when installed. A skill file does not install an authenticated API, connector, or running application. **Never invent capabilities or silently fall back to local storage.**

The app's Docker Compose deployment on a personal computer is still connected AgentBoard mode. The separate file-only fallback is not the same as local app hosting.

## Discovery and decision

1. Inspect the live MCP tool list and the schemas/permission notes for the operations needed by this command. Confirm project list/get/create as needed; role list/get/create as needed; document and ticket read/write as needed; and metadata, status, approval, or activity operations only when the command needs them. A tool name alone does not prove capability. If a needed operation is absent or ambiguous, report the blocker.
2. Connect to the app after the builder starts it through its documented Docker Compose procedure. Automatic AgentBuild launch is undefined.
3. Check the specific capability needed for this command before acting: project discovery/creation, role configuration, document/ticket reads or writes, metadata, status, and approval workflows.
4. Use verified read/write operations as the project's canonical store. Create/update each planning artifact directly in AgentBoard, store metadata fields and tags, and verify returned IDs/results. Do not create a parallel file-only project or fabricate success.
5. If AgentBoard is not installed and the user has not chosen a target, ask whether they want file-only mode or to cancel/install AgentBoard, as described in `references/local-workspace.md`.
6. If an installed app cannot start, become ready, or lacks the needed operation, report the specific blocker and stop. Do not redirect to files unless the user explicitly chooses file-only mode.
7. After an explicit file-only choice, create/use the local project. After cancel, report no changes. Do not retry fallback in the same turn.
8. If the user requested **AgentBoard-only**, respect it: do not suggest file-only creation as if authorized.

## Operation mapping

| Intent | Verified AgentBoard capability | App not installed / app failure |
| --- | --- | --- |
| Project setup | Reuse uniquely matching project or create authorized record | If not installed, ask app vs file-only target. If installed but failing, report blocker and stop. |
| Roles | Reuse/create only missing app role records | If not installed, ask target; if app fails, report blocker and stop. |
| Vision, stories, architecture, design, tickets | Read/write supported AgentBoard project/document/ticket records directly | If not installed, ask target; if app fails or lacks capability, stop without redirecting. |
| Status/review | Inspect confirmed records | Read existing files only when file-only mode was chosen; otherwise report unavailable. |
| File-only mode | Separate opt-in workspace; no implicit queue | Use only after explicit selection; never silently switch or overwrite. |

## Local implementation and evidence

Create-Screens needs a local checkout to edit frontend source and save captures, logs, and review evidence. In connected mode this checkout is the implementation workspace, not a switch to file-only storage. AgentBoard remains canonical for planning records. Reuse an existing checkout tied to the verified project; do not scaffold a second project or write duplicate planning documents. Read current planning records from AgentBoard before implementation. If no suitable checkout or required local validation context exists, ask which code repository to use or report the verification blocker; do not create a file-only project automatically.

## Idempotency and safety

Find projects by verified stable IDs or unique name; avoid duplicate records. Reuse customized roles. Do not assume a Documents page or attachment upload workflow exists. Remote actions require actual tool result confirmation. Local manifest `storage_mode: local`, `sync_state: local_only` is **not** a pending remote sync. Confirm the configured MCP service responds before reading or writing project records.

Connected mode is not a delayed file sync: commands write directly to AgentBoard. Local fallback remains independent and does not upload automatically. If a user later migrates a local project into AgentBoard, compare both sides, show conflicts, and request authorization before applying changes.
