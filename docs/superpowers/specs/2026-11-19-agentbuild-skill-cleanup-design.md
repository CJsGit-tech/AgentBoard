# AgentBuild Skill Cleanup and Install

## Intent

Make the existing AgentBuild skill safer and clear enough to install in Codex. Preserve its current product-planning and screen-building features. The three agent audits and Claude Code audit found a small set of concrete safety, consistency, and portability gaps.

## Goals

- Fix the artifact-archive symlink check and unsafe shell-argument examples.
- Clarify when a saved local-consent flag may be trusted, especially for copied or imported projects.
- Reconcile the connected AgentBoard workflow with local source-code and screen-evidence requirements.
- Define how a skill checks that the AgentBoard MCP connection supports the operation it needs.
- Require separate approval before installing the Modern Web Guidance dependency; avoid unpinned `@latest` examples.
- Correct stale paths and references, remove duplicated routing text, and add local Codex installation instructions.
- Validate the skill, then install a copy at `~/.codex/skills/agentbuild` if that destination remains unused.

## Non-goals

- Rewriting the skill or removing existing commands and resources without evidence that they are unused.
- Relaxing the independent reviewer, coverage, or evidence requirements for verified Create-Screens completion.
- Installing Modern Web Guidance or any other external dependency as part of installing this skill.
- Installing a separate Claude Code copy; this request is being handled in Codex.
- Changing the AgentBoard application or its live project data.

## Approaches

1. **Focused cleanup (selected):** Correct confirmed defects and contradictions while preserving the current command set and verification bar. This matches the user's request to clean the existing skill before installation.
2. **Broad simplification:** Rewrite the instruction system and loosen or remove strict workflow gates. This risks changing product behavior and is not needed to fix the reported defects.
3. **Install as-is:** Leaves known safety and workflow gaps in place, so it does not meet the request.

## Implementation outline

- Keep detailed rules in their owning references and leave short routing pointers in `SKILL.md`.
- Treat the AgentBoard app as canonical for planning records. Permit the checked-out code workspace and its screen evidence in connected mode without treating them as file-only storage or duplicating canonical planning documents.
- Describe capability discovery through the live MCP tool list and required operation families. If an operation is unavailable, report that blocker; do not switch storage automatically.
- Treat installation of Modern Web Guidance as a separate user-approved action. Use an explicitly selected version consistently for search, retrieval, and scan.
- Check every archive path component for symlinks before writing under project history.
- Pass project names and paths as safe arguments; ask again before writes when consent provenance is unclear for copied/imported workspaces.
- Align the role charters, host guidance, command counts, and setup consent wording with the command contracts.
- Add clear local-install steps and keep only resources that have a live caller or a clear package purpose.
- Run the skill validator and relevant existing validation checks. Do not claim that structural checks prove host behavior or screen quality.

## Constraints and assumptions

- The user selected focused cleanup.
- The destination `~/.codex/skills/agentbuild` did not exist at inspection time. Recheck before installation; do not overwrite an existing skill.
- Install only after the cleaned package passes its available structural validation.
- If Claude's independent review conflicts with an observed source fact, preserve the source evidence and document the difference.

## Open for approval

Please approve this design before implementation. Correct the Codex-only installation assumption if you also want the skill installed for Claude Code.
