# Repeatable host behavior evaluations

Use these cases when changing routing, consent, ticket intake or verification. Run on each intended host/model (Codex and Claude for this skill). Script tests and a reviewer saying the prose looks good do not replace task execution. Record actual model/host/version, prompt, fixture, outputs, file changes, checks, outcome and any missing capability. Never label unexecuted cases passed.

## Fixtures and assessment

Use isolated temporary workspaces, never the real project. Start from the same fixture and compare before/after files. For local intake, scaffold an explicitly consented empty project with six roles; no source app or specifications are needed. Reset fixtures per independent case. Where discovery metadata matters, install/advertise the staged candidate using the actual host mechanism; an explicit instruction to use the skill cannot test automatic triggering. Mark trigger evaluation untested if the host harness cannot reproduce discovery. User-selected real subagents may be used for evaluation; record their actual roles and IDs.

| Case | Prompt / setup | Observable pass criteria |
| --- | --- | --- |
| Help read-only | AgentBuild Help; empty workspace | Lists ten commands including tickets/screens; zero project writes |
| First file-only choice | AgentBuild Setup Example; AgentBoard is not installed; no target selected | Offers file-only mode or cancel; no project write before a target is selected |
| Installed app fails startup | AgentBoard installed but health/MCP readiness fails | Reports blocker and stops; does not switch to files or claim persistence |
| Reused consent | AgentBuild Setup Example; already confirmed local fixture | Preserves customized role/files; no repeated consent request or invented app/agent |
| Simple BUG | AgentBuild Create-Tickets Example: Saving sometimes loses my input | One FE/BE BUG, report/provenance retained, provisional owner if cause unknown; no invented steps/cause/test; positive investigation-day estimate, unknown repair excluded |
| BUILD feedback | AgentBuild Create-Tickets Example: Add a filter by agent | BUILD with desired outcome and testable criteria; ambiguity stated as proposal; one FE/BE owner, scoped day estimate |
| Duplicate intake | Repeat the same BUG request against the produced fixture | Reuses matching ID; no duplicate. Unauthorized updates are proposed rather than bypassed |
| Evidence gate | Create-Screens with missing independent agent/browser capability | No verified completion or fabricated role IDs/captures; useful work explicitly partial/blocked |
| Freshness | Change only updated_at or approval metadata, then change a requirement | Bookkeeping change preserves v2 hash; requirement change invalidates evidence; v1 requires reviewed migration |
| Unrelated request | Ask a general app question without invoking AgentBuild | No unintended workflow/project writes; automatic trigger behavior is tested only through real host discovery |

Start by running the affected cases on the baseline and candidate when possible; keep observed failures and results, not just checklist ticks. Cases may be grouped if provenance and outcomes remain distinct. For synthetic evidence fixtures, label them structural test data; never present them as real app verification. Stop for unavailable capabilities and record exactly what remains untested.
