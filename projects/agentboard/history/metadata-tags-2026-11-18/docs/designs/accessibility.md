# Accessibility

> Owner: Product Designer | Version: 0.1.2 | Status: draft | Last Updated: 2026-11-18

**Purpose:** Make every operation usable without color, hover or dragging.

**Related stories:** Cross-cutting

**Required context:** [Shared states](interaction-states.md).

- Use native tables; board columns have headings and lists. Ticket titles are real links, with separately labeled actions.
- Support keyboard navigation and explicit status menus; dragging cannot be the only board interaction.
- Trap focus in modal dialogs and return it to the trigger. Preserve drafts when Escape closes or prompts.
- Meet 4.5:1 normal-text and 3:1 meaningful control/focus/chart contrast. Decorative borders cannot substitute for control boundaries. Chart legends use normal text contrast.
- Minimum targets are 24px; proposed desktop controls are 36px, with spacing. Keyboard and pointer are the confirmed inputs.
- Provide chart labels and accessible count tables. Diffs use signs/labels in addition to color.
- Keep actions available at 200% zoom; allow accessible horizontal scrolling for tables, boards and diffs as desktop browser windows resize.
- Batch live announcements; do not interrupt reading with each event. Exact times and timezone are available without hover.

Verify keyboard, focus, zoom, contrast, reduced motion and screen-reader behavior in rendered screens. Token contrast alone does not prove accessibility.
