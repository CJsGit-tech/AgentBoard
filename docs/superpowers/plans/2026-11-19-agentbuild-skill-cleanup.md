# AgentBuild Skill Cleanup Implementation Plan

> **For agentic workers:** Use the approved design at `docs/superpowers/specs/2026-11-19-agentbuild-skill-cleanup-design.md`. Keep edits within the listed files and preserve the existing command set and screen-review bar.

**Goal:** Correct the reviewed safety, workflow, and portability gaps, validate the AgentBuild skill, and install it for Codex without overwriting an existing skill.

**Architecture:** Keep the current router and command-specific references. Make one small path-safety change in the artifact saver, clarify shared policy in its owning references, and install a separate copy to the standard Codex user-skill directory.

**Tech Stack:** Markdown, Python standard library, Codex skill directory.

**Spec:** `docs/superpowers/specs/2026-11-19-agentbuild-skill-cleanup-design.md`

## Global Constraints

- Preserve all existing AgentBuild commands and their established outputs.
- AgentBoard remains canonical for connected planning records; never create a silent file-only fallback.
- Screen source and evidence may live in the selected local code checkout while connected; do not duplicate canonical planning documents.
- Installing Modern Web Guidance is a separate action requiring explicit user approval.
- Never overwrite an existing `~/.codex/skills/agentbuild` installation.
- Do not claim structural validation proves host behavior or screen quality.

## Review Focus

- A symlink at `history/` must not redirect archived files outside the project.
- A copied or imported manifest must not silently prove the current user's local-write consent.
- Project names and paths must not be pasted into shell source without safe quoting.
- Connected mode must allow local source/evidence without becoming file-only storage.
- A missing guidance dependency must block screens until separately approved for installation.

---

### Task 1: Harden artifact history writes

**Files:**
- Modify: `agentboard-skill/scripts/save_artifact.py`
- Test: `agentboard-skill/tests/test_skill.py`

**Interfaces:**
- Keep the `persist(project, artifact_key, source, revise=False)` interface and existing on-disk archive layout.

- [x] Add regression tests for a symlinked `history/` parent and a dangling archive symlink.
- [x] Run both tests before the fix and confirm they expose writes through the symlinks.
- [x] Check every existing path component from `history/<artifact>` back to the resolved project root for symlinks before `mkdir` or copy; reject existing or dangling archive symlinks.
- [x] Run both regression tests after the fix and confirm the writes are rejected; preserve existing `docs/` path checks.

### Task 2: Reconcile storage, integration, and dependency rules

**Files:**
- Modify: `agentboard-skill/SKILL.md`
- Modify: `agentboard-skill/commands/create-screens.md`
- Modify: `agentboard-skill/commands/help.md`
- Modify: `agentboard-skill/references/agentboard-integration.md`
- Modify: `agentboard-skill/references/local-workspace.md`
- Modify: `agentboard-skill/references/modern-web-guidance.md`

**Interfaces:**
- `agentboard-integration.md` owns live MCP discovery and operation requirements.
- `local-workspace.md` owns local consent and file-only storage rules.
- `modern-web-guidance.md` owns dependency provenance, pinning, and screen review use.

- [x] State that connected-mode screen source and evidence use the selected code checkout; AgentBoard remains canonical for planning records, and this exception does not authorize a parallel document store or silent storage fallback.
- [x] Give a capability-discovery checklist based on the live MCP tool list and project/role/document/ticket operation families. Missing capabilities stop the dependent operation.
- [x] Require explicit approval before installing Modern Web Guidance. Replace `@latest` examples with an explicit pinned-version placeholder and require one version across search/retrieve/scan.
- [x] Align non-web guidance wording with the currently supported native/iOS targets.
- [x] Explain that scripts trust the manifest consent flag and cannot detect copies; the agent must re-ask when copied/imported provenance is known or unclear.

### Task 3: Remove stale and duplicated guidance

**Files:**
- Modify: `agentboard-skill/README.md`
- Modify: `agentboard-skill/SKILL.md`
- Modify: `agentboard-skill/commands/setup.md`
- Modify: `agentboard-skill/commands/technical-documents.md`
- Modify: `agentboard-skill/commands/design-profile.md`
- Modify: `agentboard-skill/roles/backend-programmer.md`
- Modify: `agentboard-skill/roles/frontend-programmer.md`
- Modify: `agentboard-skill/roles/code-reviewer.md`
- Modify: `agentboard-skill/references/contracts-and-examples.md`

- [x] Add the missing confirmed platform and deployment policy to `SKILL.md` and point command contracts to it.
- [x] Keep shared screen UI constraints in their owning screen reference and leave only a short pointer in `SKILL.md`.
- [x] Make shell examples require safe argv construction/quoting for project-controlled values.
- [x] Align frontend and code-reviewer role charters with Create-Screens and connected-mode report storage.
- [x] Clarify the “ten commands” count as ten project commands plus Help.
- [x] Search for the stale `AgentBoard/projects/agentboard/compose.yaml` example path (none remains); document the local Codex install path and separate Claude installation.
- [x] Replace the Codex-only validator virtualenv path with the project-local portable environment.

### Task 4: Validate and install for Codex

**Files:**
- Read/validate: `agentboard-skill/`
- Install: `~/.codex/skills/agentbuild/` (copy only after rechecking that it does not exist)

- [x] Run `python3 -m unittest discover -s agentboard-skill/tests -v` and read the results; 97 tests pass, while 10 contract tests require absent optional dependencies in `requirements-contracts.txt`.
- [x] Run `python3 agentboard-skill/scripts/validate_skill.py` and `git diff --check`; both pass.
- [x] Check helper script syntax without creating generated files.
- [x] Confirm the destination was absent before installation.
- [x] Copy the completed skill to `~/.codex/skills/agentbuild` using the authorized filesystem escalation.
- [x] Compare installed files with the repository source; all 75 files match byte-for-byte.
