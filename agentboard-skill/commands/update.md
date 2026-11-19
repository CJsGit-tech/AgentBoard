# Contract: Update

## Purpose

Carry a change request through the affected planning artifacts of an existing project. The Orchestrator uses the relevant command contracts for artifact format and quality.

- `AgentBuild Update <ProjectName> --preview` proposes changes. Preview is the default.
- `AgentBuild Update <ProjectName> --apply <plan-id>` applies an exact plan previously shown to and selected by the user.

## Preconditions

An existing project and a requested change. Apply also requires a previously reviewed plan.

## Owner

Orchestrator.

## Required context

Read the project index, the relevant artifact contracts, and the applicable storage and revision guidance.

## Execution

### Preview

1. Resolve the existing project and its authorized storage using the standard integration rules. Start with indexes and follow explicit links to relevant artifacts. Inspect source read-only when it can confirm reported behavior or implementation coverage. State evidence gaps.
2. Map each request to its affected vision, stories, architecture, design and tickets as applicable. Prefer updating the existing artifact by stable identity. Create a follow-up ticket when new work would change the scope or closure evidence of an existing ticket. Preserve unrelated material.
3. Show each proposed update or create, its reason, and a before/after excerpt or proposed content. Include dependencies, unresolved decisions, and any independently actionable subset. Capture the target project, storage mode, exact proposed payloads, existing record identities and base revisions (or file content hashes) in the conversation under a plan ID. Use proposed titles for new records until the store allocates real IDs.
4. Keep preview read-only. Do not write project records, plan files or code, submit approval requests, or inspect secrets. Label any partial preview and its missing input.

Use this format in the user-facing preview instead of a summary table. Keep the plan ID and verification status above the task blocks.

```markdown
TASK: <description>

<filename>:

- From: <current behavior or content>
- To: <proposed behavior or content>
```

Repeat the task heading for each requested change and the filename block for each affected artifact. For connected records, use the source filename when available and the record title otherwise. For a new artifact, write `From: New artifact` and put the proposed content under `To`. Keep unresolved decisions with the task they affect.

### Apply

1. Resolve the plan ID to the exact reviewed plan in the current conversation. If the plan or its baseline is unavailable, regenerate a preview. Hold changes that depend on an unresolved material decision.
2. Recheck the project, target revisions and duplicates before writing. If a baseline changed, refresh the affected proposal and request review of the revised plan before applying it. Use revision preconditions for updates when supported. If the available write path cannot enforce a required revision check, report the blocker.
3. Apply only the selected plan through verified MCP in connected mode, or the authorized file workflow in confirmed file-only mode. Follow ordinary update approvals and revision history. Use stable operation keys for retried creates when supported. Resolve links from returned IDs and wait for prerequisites before applying dependent changes.
4. Report each confirmed create or update, pending approval, conflict, or failure. On partial completion, retain returned IDs and re-read state before retrying. Claim completion only after verifying the requested records and links.

Update covers planning records. Implementation, project migration and reconciliation between storage modes require separate instructions.

## Output artifacts

A conversation preview, or the confirmed planning records and an itemized apply result.

## Acceptance checks

The preview makes each proposed change reviewable. Apply preserves stable identities and rejects stale baselines.

## Persistence updates

Only apply mutates project storage. The preview plan lives in the conversation.

## Failure handling

When identity, connection, or approval cannot be verified, report the affected items and use the standard storage and approval rules. When a plan is partially applied, report the actual per-item state.
