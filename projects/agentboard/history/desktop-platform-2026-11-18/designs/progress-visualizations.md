# Progress visualizations

> Owner: Product Designer | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Show measured ticket progress without implying agent execution performance.

**Related stories:** US-009, US-012

**Required context:** [Interaction states](interaction-states.md) and [accessibility](accessibility.md).

- Show four status counts; clicking a status applies its existing ticket filter.
- Use a horizontal stacked bar with equal units per ticket, labeled legend and accessible count table.
- Label Done / total as task completion, not product completion. No tasks does not equal 100% completion.
- Show Needs approval as a separate count; exclude it as a status segment.
- Label aggregates Project totals unless the backend explicitly defines filtered aggregates.
- Do not add burndown, throughput, time series or live utilization without supporting data requirements.

## Unresolved contracts

Architect: approval-only filtering and filtered overview aggregates are not currently defined. Show approval badge/count without a fabricated filter action. Unavailable counts use the error state, never zero.
