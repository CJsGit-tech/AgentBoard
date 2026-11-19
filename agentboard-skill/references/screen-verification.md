# Create-Screens builder, reviewer and evidence gate

## Required execution roles

The orchestrator launches a real builder using project `agents/frontend-programmer.md` and a separate reviewer using project `agents/code-reviewer.md`. Both read `agents/product-designer.md` and the relevant design rules. Read actual role files before dispatch; they are instructions, not proof agents ran. Record real invocation IDs and role paths. The reviewer must be a distinct agent, must not author the implementation, and must inspect actual source, browser output and requirements rather than trust the builder summary. No extra designer agent is required by default.

This explicit command policy enables the builder/reviewer pair for Create-Screens only. Other commands retain their delegation rules. If subagent execution or required project roles are unavailable, continue useful work only as partial/blocked and report the missing capability. Self-review cannot satisfy this gate. Missing roles may be created from skill role templates within an authorized project; do not overwrite custom charters silently.

## Workflow

1. Before building, derive the complete screen/state/action checklist from stories and design; assign stable screen/check IDs. Builder implements all screens and supplies source paths, component map, captures and command output. The orchestrator maintains the inventory and scope.
2. Run the actual stack's build, type checking where applicable, automated browser/UI tests, and `check_outputs.py --strict`. UI checks cover every required screen render, runtime errors, key actions, navigation/return paths, shared mock state and story-specific exceptions. Add meaningful interaction assertions; screenshot existence or a page-load smoke test is insufficient. Record exact command, working directory, exit code, UTC completion time and saved output. Retain test configuration/scripts so runs are reproducible. Native targets use their appropriate automated UI harness instead of browser tests.
3. The reviewer independently reconciles inventory against all requirements to catch omitted screens; reruns automated checks, walks key flows, inspects captures at target window sizes and reviews component boundaries, focus and dropdown rules. It writes `reviewer-report.md` with requirement IDs, inspected evidence, failures, severity and verdict. The builder cannot write the reviewer verdict. Automated pass does not replace visual review.
4. Reviewer findings return to the builder. If the builder has finished its turn, explicitly resume it with the runtime’s follow-up task operation; merely queuing a message is not proof correction work restarted. Confirm actual builder execution before waiting for fixes. After fixes, rerun affected checks plus checks impacted by shared code; reviewer reinspects the changed source and affected flows. Reuse valid evidence for unchanged work but refresh the final source fingerprint only after confirming all retained evidence is still applicable. Do not claim old checks ran on a new revision. Record this applicability assessment in the reviewer report. Unresolved required items prevent completion. Avoid an unbounded review loop: report a precise blocker if progress requires external input.
5. Run the read-only evidence gate on the final source. Only automated passes, complete required coverage, independent reviewer pass and a passing gate allow the outcome **verified_pending_review**. Only the user can approve design. Missing/failed checks mean partial or blocked, with affected screens named. Optional gaps require explicit rationale; required checks cannot be relabeled optional to pass.

## Saved evidence

Use `docs/designs/screens/evidence/<run-id>/` for actual logs and the reviewer report; captures remain in `docs/designs/screens/captures/`. Preserve prior runs, but keep only one frontend implementation. `evidence/latest.json` identifies the final evaluated run. Never fabricate logs, screenshots, invocation IDs or timestamps.

Generate the fingerprint with:

```sh
python3 <skill>/scripts/check_screen_evidence.py --project <project> --fingerprint <frontend-source-root>
python3 <skill>/scripts/check_screen_evidence.py --project <project> --context-fingerprint
python3 <skill>/scripts/check_screen_evidence.py --project <project>
```

Fingerprint includes frontend source/config/tests/lockfiles, excluding dependencies, build outputs and evidence. Use a project-relative frontend directory covering relevant source; never narrow it to hide changes. Build dependencies and external environment are not certified by this hash.

`latest.json` uses schema_version=1 and these fields:

- `status`: verified_pending_review only after real checks/review.
- `source_root`, `source_fingerprint`: canonical frontend path and computed hash.
- `context_fingerprint_version`: 2. `context_fingerprint`: computed relevant-context hash; reviewer records the same hash. Version 2 normalizes known document Version/Last Updated/Status metadata and manifest timestamps/versions/lifecycle states/remote IDs; excludes review outputs, derived ticket navigation tables and ticket progress/estimates/investigation results; retains human ticket-index policy prose; retains ticket outcome/criteria/context, other requirement documents, role content and semantic manifest settings. This is conservative scope, not automatic semantic relevance inference. New requirements invalidate evidence even if source is unchanged. Existing version-1 hashes need an independent applicability/coverage review before migration; never rehash solely to make the gate pass. Changed skill verification requirements also need review and are not authenticated by the project-context hash.
- `builder`: real `agent_id`, `role_file` = agents/frontend-programmer.md.
- `reviewer`: different real `agent_id`, `role_file` = agents/code-reviewer.md, independent=true, verdict=pass, current source_fingerprint, and project-relative `report` path.
- `checks`: entries with unique `id`, `kind` (build/typecheck/ui/output-consistency/legacy-scan), status, command, cwd, exit_code, finished_at, project-relative log. Typecheck alone may be not_applicable with explicit reason where the confirmed stack has no separate type check; preserve its rationale log. Reviewers record rerun commands too.
- `screens`: each inventory entry has unique id, requirements references, status=verified, source path, nonempty capture paths, and ui_checks referencing passing UI check IDs. Include important state/action coverage in the linked reviewer report and inventory.
- `unresolved_required_items`: empty only when every required item is resolved.

Gate validates saved structure, files, check outcomes, distinct agent identities and source freshness. It cannot authenticate agent IDs, infer missing requirements, prove logs are genuine, inspect screenshot pixels or certify behavior. Those remain mandatory independent-review responsibilities. Never present this gate or the skill's own unit tests as application verification.

## Required guidance review

Follow `modern-web-guidance.md`. Both builder and reviewer read the installed dependency and relevant retrieved guides. Record actual search/retrieve commands and a final guidance findings/fixes/verification matrix. Applicable unresolved findings block completion. `latest.json.guidance` requires status=reviewed, cli_version, skill_version, nonempty guides and report; non-web applicability must be explicitly justified.

## Scan policy

Follow the [mandatory scan and feedback-resolution policy](modern-web-guidance.md#mandatory-scan-and-feedback-resolution-policy). That reference owns scan cadence, applicability, fix/recheck, evidence fields and blocking behavior; this document owns execution-role separation and overall evidence requirements.
