---
name: "T-026 — Keep keyboard focus inside controls"
description: "Keeps keyboard focus inside the pairing field and document tag checkbox."
kind: "ticket"
tags: ["feature:document-management", "concern:accessibility"]
---

# T-026 — Keep keyboard focus inside controls

Role: FE
Type: BUG
Status: Done
Verification: Fixed
Assignment: Confirmed
Depends on: None
Estimate (days): 0.25
Estimate scope: Repair
Estimate basis: Scoped CSS repair, packaged web rebuild, and keyboard and zoom checks in Chrome.

## Outcome

Both controls visibly indicate keyboard focus within their bounds.

## User Report

Discovered during the connected release check. Focusing the pairing field showed an outer outline. At 200% browser zoom the document tag checkbox stretched across the filter row and its focus indicator stretched with it.

## Investigation

The pairing field had a specific focus override that drew an outer outline. The checkbox inherited global input dimensions. The pairing field now uses the shared inset style, and the document tag checkbox uses dimensions scoped to the tag filter.

## Acceptance Criteria

- Keep keyboard focus visibly inset in the connected pairing field.
- Keep the tag checkbox and its visible focus indicator within the checkbox at 200% Chrome zoom. Verify keyboard toggling.

## Context

- [T-020 — Verify persisted desktop journeys](T-020-verify-persisted-desktop-user-journeys.md)
- [Control styles](../../frontend/src/styles.css)

## Completion Evidence

The pairing field rendered with visible inset focus and no outer outline. At 200% Chrome zoom the checkbox measured 16 × 16 CSS pixels, drew a 2-pixel inset focus indicator, and responded to Space. See the [connected browser evidence](../review-report.md#local-runtime-evidence).
