# Required Modern Web Guidance dependency

Official docs: https://developer.chrome.com/docs/modern-web-guidance
Source: https://github.com/GoogleChrome/modern-web-guidance-src
Installable distribution: https://github.com/GoogleChrome/modern-web-guidance/tree/main/skills/modern-web-guidance

Create-Screens requires the official `modern-web-guidance` skill installed and readable. The source repository name is not the installed skill name. Resolve the actual readable installed entrypoint using `scripts/check_screen_evidence.py` discovery: project/ancestor `.agents/skills` or `.claude/skills`, `$CODEX_HOME/skills`, then user `.agents/skills`, `.claude/skills` and `.codex/skills`. `AGENTBUILD_GUIDANCE_SKILL` or `--guidance-skill` explicitly selects an entrypoint/folder; an invalid override fails without silently falling back. Discovery checks skill identity/readability, not publisher authenticity: use the official distribution below and verify provenance when installing. Do not move a working installation just to match an example path. If missing, explain the requirement and ask for explicit approval before installing it; invoking AgentBuild or approving project storage does not authorize installing another skill or dependency. If installation or retrieval is unavailable, report a dependency blocker rather than silently skipping it. Read its SKILL.md before implementation/review. Other runtimes should use the official installer for that agent. Do not copy the entire source repository into the app.

## Commands and selective reading

For web UI work, run focused 2–5 word searches at the start of each relevant feature batch, then retrieve matching guides and relevant discipline guides. Reuse already retrieved unchanged guidance; do not load the entire catalog for every edit. Follow the installed skill's version flag, output-file handling, browser-support and fallback instructions.

```sh
npx -y modern-web-guidance@<approved-version> search "manage modal focus" --skill-version <installed-skill-version>
npx -y modern-web-guidance@<approved-version> retrieve "dialog,accessibility"
npx -y modern-web-guidance@<approved-version> search "responsive data table" --skill-version <installed-skill-version>
npx -y modern-web-guidance@<approved-version> retrieve "responsive-table"
```

Read actual descriptions/IDs before retrieval; never invent IDs. Rephrase an unsuccessful search once with a concrete primitive, then optionally list. Do not opt into volatile features/origin trials without a requirement. Preserve confirmed project/browser policy over illustrative snippets. Obtain and record approval for a specific package version before `npx` executes it; use that same pinned version for search/retrieve/scan and do not silently upgrade mid-review.

## Guidance → critique → improvement loop

Builder retrieves applicable guides and records guide ID, version, command output and concrete implications. Reviewer compares actual source and rendered behavior against them, creating requirement-linked findings with evidence. Evaluate applicability first: do not blindly apply a guide example, force unrelated features or chase a zero scan count. For each finding, record applicability, severity, source/screen, fix, and regression check; non-applicable recommendations require a reason. Any required applicable finding must go to the builder for correction and back to the reviewer for verification. Re-run affected checks and update evidence after fixes. A guidance command returning text is not a critique verdict or proof of compliance.

Save search/retrieve logs and the guide review matrix under the screen evidence run. `latest.json.guidance` records status=reviewed, cli_version, skill_version, guide IDs and a project-relative report. For iOS/native targets, retain the installed dependency but record status=not_applicable and a platform reason rather than forcing web APIs into native UI. The independent report must assess final guide compliance alongside product requirements; unresolved applicable findings block verified completion.

## Mandatory scan and feedback-resolution policy

This is the owning policy for the user-required scan. At the end of **every Create-Screens work turn and fix iteration**, execute `legacy-scan <authored-frontend-path> --json` and have the independent reviewer assess applicability against actual source and the guidance rubrics. This overrides the upstream modernization-only default. Do not scan dependencies/generated builds. It covers a subset of guidance, not overall UI correctness. It does not apply to unrelated Help, chat, ticket planning or skill maintenance.

Save exact command, scope, version, UTC time, exit status and raw JSON. Record current-source `latest.json.legacy_scan` (reviewed status, source_fingerprint, raw_output, report) and a passing check of kind legacy-scan. Missing execution/review blocks verified completion. A clean scan requires no invented fixes or unnecessary UI reruns when source is unchanged.

Repeat scan/review → builder corrections → affected automated/render checks → rescan → independent re-review until every applicable required finding is verified resolved. The reviewer confirms actual source/behavior, not a builder claim. Track stable finding IDs, applicability, severity, owner, status, changes and evidence. Preserve justified fallbacks/false-positive rationale; never modify safe code or scan internals to force zero findings. Required scope cannot silently become optional; only the user can waive a requirement. Regressions enter the same loop.

Resume completed agents using the runtime's follow-up operation when assigning fixes, as specified in `screen-verification.md`. If progress needs unavailable capabilities or an external decision, preserve the findings and report partial/blocked. Stop when all applicable required findings are resolved; do not keep iterating merely to invent more work. Human design approval remains separate.
