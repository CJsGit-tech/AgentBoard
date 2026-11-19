# AgentBuild command contracts — v2

A **command contract** defines how an instruction is executed and persisted. A **document template** defines what the resulting artifact contains. A role charter defines who is accountable.

Every `commands/*.md` contract includes:

1. **Purpose** — expected outcome.
2. **Preconditions** — genuine hard requirements, not a mandatory app connection.
3. **Owner** — accountable role (not proof a subagent launched).
4. **Required context** — project inputs, artifacts and references to load.
5. **Execution** — concrete task steps and decisions.
6. **Output artifacts** — exact project-relative paths.
7. **Acceptance checks** — automated and semantic tests.
8. **Persistence updates** — write to the canonical AgentBoard project by default, or the explicitly selected local-only project. Verify the actual saved record IDs or local files; update the local manifest only in local-only mode.
9. **Failure handling** — what is actually blocking versus optional.

## Shared persistence contract

- A named project can be created locally only **after user approval** of local storage. Default proposed path: `<cwd>/projects/<slug>`.
- On missing AgentBoard capability: **ask the user Yes/No before proceeding**. No filesystem writes before consent; after `Yes` call `scripts/scaffold_project.py --user-approved-local`. Existing manifest approval allows subsequent local commands without repeated prompts.
- For document commands: use a verified AgentBoard connection as the canonical target when installed; author and persist directly through supported app operations, then verify returned record IDs and metadata. If AgentBoard is not installed and the user has not chosen a target, ask whether to use file-only mode or cancel. If an installed app fails or lacks a required operation, report the blocker and stop unless the user explicitly chooses file-only mode. Save chosen file-only work through `scripts/save_artifact.py` or the folder workflow. For local single-file artifacts, the helper updates the manifest to `draft` with a semantic version. For local folder artifacts, preserve individual file history and update file/index/manifest metadata explicitly; follow `references/document-folders.md`. Run the applicable validator; semantic review is separate.
- Do not create empty product documents as part of Setup.
- Repeated Setup is safe and does not overwrite customized agent charters or documents.
- A changed existing artifact requires explicit revision/archiving (`--revise`); don't silently overwrite approved documents.
- Never mark files approved merely because an automated script passed.
- Direct AgentBoard writes, agent spawning and local-project migration require actual supported capabilities and explicit authorizations; no implied success. Normal connected document commands are direct app writes, not a later sync.

## Output collection

| Artifact | File | Owner | Depends on |
| --- | --- | --- | --- |
| vision | AgentBoard document record, or `docs/product-vision.md` in local mode | Product Manager | Project concept |
| stories | AgentBoard document records, or README + individual files in local mode | Product Manager | vision |
| architecture | AgentBoard document records/diagram, or README + topic files in local mode | Solution Architect | vision, stories |
| architecture-svg | `docs/technical-architecture/system-architecture.svg` | Solution Architect | architecture |
| design | AgentBoard document records, or `docs/designs/README.md` in local mode | Product Designer | vision, stories |
| tokens | `docs/designs/design-tokens.json` | Product Designer | design |
| screens | canonical frontend source + `docs/designs/screens/README.md` coverage/captures | Frontend Programmer | vision, stories, design, confirmed stack |
| tickets | AgentBoard ticket records, or README + one `T-###` file per ticket in local mode | Product Manager; FE/BE execution owner per ticket | report or relevant existing scope |
| review | `docs/review-report.md` | Code Reviewer | available artifacts |

The local `project-manifest.json` is the authoritative record **for local mode**, not merely a support index. In a verified AgentBoard mode, rely only on confirmed remote records. See `references/local-workspace.md`.
