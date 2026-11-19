# Script-assisted output consistency

Use deterministic scripts for mechanical consistency; humans/agents still own meaning, design decisions and runtime verification. Keep ordinary files and the minimal-reading layout.

## Sources of truth

| Content | Authoritative source | Script-derived/checkable output |
| --- | --- | --- |
| Story ID, title, associated features | Individual US-### Markdown file | Story README navigation |
| MCP name, permission, schema refs | contracts/mcp/tools.json | MCP README navigation; hint consistency |
| Example/schema/operation binding | contracts/manifest.json + schemas/OpenAPI | Typed example validation and declared case coverage |
| Technical topic selection | Confirmed document plan + catalog | Skeleton structure and document coverage checks |
| Architectural meaning, tradeoffs and policies | Authored topic documents | Semantic review; not inferred by scripts |

Keep human-authored topic files focused on responsibility and policy; link to generated inventories instead of repeating full tool-name lists or fixed operation counts. Do not edit generated navigation rows to change requirements. Edit their source, then synchronize. Do not generate business rules from examples or silently rewrite architecture to satisfy a check.

## Default completion workflow

1. Author/update canonical story, schema and topic files. Preserve history and update metadata using the existing workflow.
2. Update the contract inventory and explicit required example cases when interface behavior changes.
3. Run navigation synchronization explicitly.
4. Run the single read-only consistency gate in strict mode.
5. Resolve findings, then perform the separate semantic/diagram review before reporting quality.

```sh
<validation-python> <skill-root>/scripts/sync_navigation.py --project <project> --write
<validation-python> <skill-root>/scripts/check_outputs.py --project <project> --strict
```

For a read-only preview use sync_navigation.py --check (also the default). For machine-readable results use check_outputs.py --json. The gate combines project/profile/contracts/examples checks, navigation drift and counts. It does not download dependencies or mutate files. Resolve a working interpreter with the dependencies in `requirements-contracts.txt`; do not assume a preinstalled Codex-specific environment. A known working environment can be reused. When setup is needed and authorized, create an isolated environment in the selected project/workspace:

```sh
python3 -m venv <project>/.venv-agentbuild
<project>/.venv-agentbuild/bin/python -m pip install -r <skill-root>/requirements-contracts.txt
```

Use that environment's Python as `<validation-python>`. On Windows its executable is `Scripts/python.exe`; on macOS/Linux it is `bin/python`. Check imports before claiming the validator is available. Setup installs packages and writes files, so it follows the existing permission/storage boundary. Missing Python/network/dependencies is an actionable blocker, not permission to skip checks. Standard-library-only helpers can use any supported Python without installing contract dependencies.

## Safe navigation blocks

Existing authored README content is never guessed to be replaceable. Put these standalone markers around only the intended table:

```html
<!-- agentbuild:stories:start -->
... story navigation table ...
<!-- agentbuild:stories:end -->
```

Use `mcp-tools` instead of `stories` for the MCP index. Markers inside fenced examples do not authorize replacement. Missing, ambiguous or reversed markers fail without writing. New README files may be created with marked blocks; authors must supply/check the usual artifact metadata. Writes require the existing project-scoped local-storage consent. Synchronization derives rows from source files; it preserves human introductions/notes outside markers and checks source text before replacement. Do not run it during concurrent editor changes. Files are replaced individually; this is not a multi-file transaction, snapshot system, or document storage engine.

To adopt existing indexes, inspect the intended table and add the markers explicitly; do not surround explanatory tables or policies. New templates include the markers. The script also refuses duplicate story IDs, missing example bindings, missing schema files and unsafe/symlink paths.

## Stronger contract checks

- Duplicate JSON keys are errors rather than last-value-wins parsing.
- Every declared MCP tool retains input/output example coverage.
- An explicitly supplied readOnlyHint must be boolean and agree with the declared read/create/approval-required permission. Hints still do not enforce authorization.
- Required workflow outcomes can be declared on a tool, for example `"x-agentbuild-required-outcomes": ["success", "approval_required", "rejected", "error"]`. Examples must contain each outcome and pass the real output schema.
- OpenAPI operations can declare `"x-agentbuild-required-examples": {"request": true, "responses": ["201", "409"]}`. Statuses must exist on that operation and have bound examples.
- Duplicate identical example bindings fail. Data bindings must target inventoried, schema-bearing nodes; metadata or definition maps cannot act as permissive stand-ins.

Choose case requirements from real workflows during authoring; the script cannot determine which business edge cases matter. Removing or weakening a coverage declaration is a design change requiring review, not a way to make validation pass.

## Limits

The combined gate reports consistency of existing outputs, not completion of artifacts that were never started. Legacy folders remain supported. It cannot prove approval enforcement, aggregate counts, cross-record foreign keys, byte-size limits, client interoperability, or that reviewers performed the recorded review. Do not translate a green structural result into human approval or runtime correctness.
