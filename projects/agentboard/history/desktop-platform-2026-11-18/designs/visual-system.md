# Visual system

> Owner: Product Designer | Version: 0.1.1 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Apply a quiet workspace with visible exceptions.

**Related stories:** Cross-cutting

**Required context:** [Tokens](design-tokens.json) and [accessibility](accessibility.md).

## Rules

- Confirmed direction: clean, minimal; effective progress visualizations and operational tables/boards. Palette, dimensions and defaults remain proposals.
- Use neutral surfaces, strong hierarchy and restrained blue emphasis. Avoid gradients, oversized KPI cards, decorative donuts, nested card grids and productivity scores.
- Tokens are authoritative for light/dark colors, typography, spacing, radii and motion; do not duplicate values here. System theme is proposed; retain local preference without resetting forms.
- Use system fonts, 16px body, 14px table text, 12px timestamps, 18–20px sections and 24px page titles. Use tabular numbers; monospace only for identifiers/code/diffs.
- Use 4/8/12/16/24/32px spacing, 24px desktop or 16px narrow gutters; shadows only for overlays.
- Status always has a label and shape: Planned circle, In progress partial circle, Blocked triangle, Done check. Needs approval uses a separate shield badge.
- Show short IDs as secondary identifiers; do not invent stored ticket codes or confuse planning story IDs with tickets. Exact timestamp and timezone must be available without hover.

## Review

Product owner must review table-first defaults, palette, System theme and proposed dimensions. Validate representative dense screens before implementation; the architecture SVG is a structural reference, not a UI palette.
