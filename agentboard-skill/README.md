# AgentBuild

AgentBuild has ten project commands plus Help. It builds confirmed-stack screens with mock data and creates engineering tickets. Its entrypoint is [SKILL.md](SKILL.md); that file's command table and linked contracts are authoritative.

```text
AgentBuild Help
AgentBuild Setup "Project"
AgentBuild Vision-Document "Project"
AgentBuild User-Stories "Project"
AgentBuild Technical-Documents "Project"
AgentBuild Design-Profile "Project"
AgentBuild Create-Screens "Project"
AgentBuild Create-Tickets "Project"
AgentBuild Update "Project" --preview
AgentBuild Update "Project" --apply <plan-id>
AgentBuild Status "Project"
AgentBuild Review "Project"
```

Install the whole folder through the current host's skill installation mechanism. For a local Codex install, copy `agentboard-skill/` to `~/.codex/skills/agentbuild/` only if that destination does not already exist; review an existing installation before replacing it. Claude uses a different discovery location. For distribution, exclude `__pycache__` and other generated files. No skill creates actual agent processes or authenticated app integrations merely by being installed.

First-time local storage requires explicit project-scoped consent; subsequent commands reuse it. Setup creates a manifest, six role charters and an empty docs folder. Documents, screens and tickets are created only by their commands. Revisions preserve history; local mode never implies pending remote synchronization.

Use command-specific references for output formats, dependencies and verification. Create-Screens requires Modern Web Guidance, real independent execution roles and saved runtime evidence. Create-Tickets accepts simple reports and routes FE/BE, BUG/BUILD work with day estimates, one file per ticket. Neither ticket planning nor screen verification claims production backend implementation.

Checks: run `scripts/validate_skill.py`, the tests under `tests/`, and the host's skill-format validator. Contract-output validation setup is documented in `references/output-consistency.md`. Repeatable behavioral evaluations are specified in `references/behavior-evaluations.md`; unit tests do not establish agent behavior.
