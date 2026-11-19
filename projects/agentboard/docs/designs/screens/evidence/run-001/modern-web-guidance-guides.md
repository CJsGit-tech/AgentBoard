--- Guide for dialog ---
# Dialog

## Overview

Use the native `<dialog>` element for modal and non-modal dialogs. It provides the accessibility semantics, focus handling, top-layer rendering and `Esc` handling that custom overlays have to rebuild by hand.

## Choose the overlay type

Pick the first rule that matches. If unsure, use Rule 1.

### Rule 1: The overlay interrupts the user and blocks the page (default)

Use for confirmations, forms, sign-in, destructive actions, and any "modal", "dialog", "lightbox" or "popup" request that does not say otherwise.

Use `<dialog>` opened as a modal, declaratively with `command="show-modal"` (see `declarative-dialog-popover-control` (via `npx -y modern-web-guidance@latest retrieve "declarative-dialog-popover-control"`)) or from script with `showModal()`.

```html
<button type="button" command="show-modal" commandfor="confirm">Delete</button>

<!-- MANDATORY: no role="dialog" or aria-modal; the native modal already provides them -->
<dialog id="confirm" aria-labelledby="confirm-title">
  <h2 id="confirm-title">Delete this item?</h2>
  <form method="dialog">
    <button value="cancel" autofocus>Cancel</button>
    <button value="delete">Delete</button>
  </form>
</dialog>
```

The browser provides: inert page, focus containment, top layer, `::backdrop`, `Esc` and back-gesture dismissal, and focus return to the invoker.

- **DON'T** add `role="dialog"`, `aria-modal`, a focus trap, `inert` toggling or an `Esc` handler.
- **DON'T** open it with `show()` or the `open` attribute.
- **DO** stop the page scrolling behind it with the CSS below. See `prevent-page-scroll-under-modal-dialog` (via `npx -y modern-web-guidance@latest retrieve "prevent-page-scroll-under-modal-dialog"`) for the details.
- **DON'T** lock scrolling with `overflow: hidden` or `position: fixed` on `html` or `body`.

```css
/* MANDATORY (both rules): without them, scrolling over the backdrop or inside the dialog scrolls the page behind it */
dialog:modal {
  overscroll-behavior: contain; /* stops scroll gestures in the dialog chaining to the page */
}
dialog::backdrop {
  overflow: hidden; /* ::backdrop is not a scroll container by default, so it would ignore overscroll-behavior */
  overscroll-behavior: contain;
}
```

Not for menus or tooltips: see Rule 3.

### Rule 2: The user keeps working in the page while the panel is open

Use for find bars, inspectors, palettes and compose panes that are still dialogs semantically.

Use `<dialog popover>` for a top-layer panel with popover dismissal (`auto` light-dismisses, `manual` does not). Use `dialog.show()` only when the panel must not be in the top layer.

```html
<button type="button" popovertarget="find">Find</button>
<dialog id="find" popover="manual" aria-labelledby="find-title">
  <h2 id="find-title">Find</h2>
  <input type="search" aria-label="Search">
  <button type="button" popovertarget="find" popovertargetaction="hide">Close</button>
</dialog>
```

The page stays interactive and is not made inert.

- **DO** include a visible close button.
- **DON'T** use `showModal()`, which blocks the page.

Not for blocking confirmations: see Rule 1.

### Rule 3: The overlay is not a dialog

Use for menus, dropdowns, tooltips, hovercards and toasts.

Use a semantic element with the `popover` attribute, not `<dialog>`.

```html
<button type="button" popovertarget="menu">Actions</button>
<ul id="menu" popover>
  <li><a href="/rename">Rename</a></li>
</ul>
```

## Choose how it can be dismissed

The default depends on how the dialog is opened. If `closedby` is absent or invalid, `showModal()` behaves as `closerequest` and any other way of opening behaves as `none`.

- **Esc and back gesture only (modal default):** set nothing, or `closedby="closerequest"`.
- **Also click outside to close:** use `closedby="any"`.
- **Only the developer closes it (for example a form with unsaved changes):** use `closedby="none"` and add a confirmation path. See Closing below.

## Guidelines

### Accessible name and initial focus

- **DO** name every dialog with `aria-labelledby` pointing at its heading, or `aria-label` when there is no visible title.
- **DO** put `autofocus` on the primary control or first field.
- **DO** put `autofocus` on the safe action (such as Cancel or Keep) in a destructive confirmation.
- **DON'T** write code to return focus on close. The browser returns it to the invoker.

### Opening

- **DO** open declaratively with `command="show-modal"` and `commandfor` on a `<button>`. See `declarative-dialog-popover-control` (via `npx -y modern-web-guidance@latest retrieve "declarative-dialog-popover-control"`).
- **DO** use `dialog.showModal()` when opening from script.

### Closing

- **DO** close with `<form method="dialog">` buttons or `command="close"`.
- **DO** choose `closedby` deliberately: `any` (light dismiss and `Esc`), `closerequest` (`Esc` only, the modal default) or `none` (developer-controlled close only).
- **DO** use `command="request-close"` or `requestClose()` for Cancel buttons that must honor unsaved-changes logic. They fire `cancel` first and ignore `closedby`.
- **DO** treat `closedby` as progressive enhancement. `Esc` and the mobile back gesture already close modals without it.

### Hooking into close

- **DO** read `dialog.returnValue` in a `close` listener to learn which button was used, then reset it with `dialog.returnValue = ''`. `Esc` and other close requests set no value, and browsers differ on whether they clear the previous one, so without the reset a stale value can leak. Treat `''` as "dismissed without choosing".
- **DO** use `cancel` to intercept `Esc` and `request-close`, but do not rely on `preventDefault()` for repeated `Esc` presses without user activation.
- **DO** use `closedby="none"` with an explicit confirmation step for dirty forms.
- **DO** tell the user why the dialog stayed open when `cancel` is prevented: show a visible message and reference it with `aria-describedby` from the control that receives focus (such as Discard), so a screen reader reads it when focus moves. Without it, focus moving to a new button announces only that button's name.
- **DON'T** let the confirmation move controls under the pointer. Reserve the message's space (hide it with `visibility`, not `display` or `hidden`) and add the destructive button where existing buttons do not move (for example first in a right-aligned row), so a second click at the same spot cannot discard the user's changes.

### Non-modal dialogs

- **DO** use `<dialog popover>` (`auto` or `manual`) for a top-layer panel, and `dialog.show()` when you do not want the top layer.
- **DO** include a visible close button in every non-modal dialog.

### Backdrop and styling

- **DO** style `::backdrop` and use `dialog:modal` to target modal-only styles.
- **DO** leave animation to `animate-to-from-top-layer` (via `npx -y modern-web-guidance@latest retrieve "animate-to-from-top-layer"`), dragging to `drag` (via `npx -y modern-web-guidance@latest retrieve "drag"`), and reparenting to `persistent-top-layer-ui` (via `npx -y modern-web-guidance@latest retrieve "persistent-top-layer-ui"`).
- **DON'T** set `display` on `dialog` unconditionally. It overrides the closed state. Scope it with `dialog[open]`.

### Accessibility

- **DON'T** add `role="dialog"`, `aria-modal`, a manual focus trap or `inert` toggling to a native modal.
- **DO** use a native `<button>` with an accessible name for close controls.
- **DO** use one consistent heading level for dialog titles.

## Fallback strategies

### `closedby` (`dialog-closedby`)

Browser support for <dialog closedby>: Limited availability.
Supported by: Chrome 134 (Mar 2025), Edge 134 (Mar 2025), and Firefox 141 (Jul 2025).
Unsupported in: Safari.

Without `closedby`, a modal still closes with `Esc` and the back gesture; only click-outside is lost, so this is graceful degradation. `closedby="none"` is ignored the same way: `Esc` fires `cancel` and then closes the dialog. Keep the unsaved-changes guard in a `cancel` handler, not in `closedby="none"` alone, so it also protects where `closedby` is missing. If your Baseline target requires light dismiss, add this where `closedby` is missing:

```js
if (!('closedBy' in HTMLDialogElement.prototype)) {
  // Test the pointer position, not event.target: the <dialog> is also the target for its own
  // padding and the gaps between its children, so a target check would close on those clicks
  const outside = (e, dialog) => {
    const r = dialog.getBoundingClientRect();
    return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
  };
  for (const dialog of document.querySelectorAll('dialog[closedby="any"]')) {
    let pressedOutside = false;
    dialog.addEventListener('pointerdown', (e) => { pressedOutside = outside(e, dialog); });
    // Require the press and the release outside, so a text-selection drag that ends on the backdrop does not dismiss
    dialog.addEventListener('pointerup', (e) => { if (pressedOutside && outside(e, dialog)) dialog.close(); });
  }
}
```

### `overscroll-behavior`

Browser support for overscroll-behavior: Limited availability.
Supported by: Chrome 144 (Jan 2026), Edge 144 (Jan 2026), and Firefox 150 (Apr 2026).
Unsupported in: Safari.

Treat scroll containment as progressive enhancement. Do not feature-detect it: `@supports` reports the property as supported even where non-scrollable containers ignore it. Where it is not enforced, the dialog still contains scroll whenever its own content overflows, and `showModal()` still makes the page inert. Do not fall back to `overflow: hidden` or `position: fixed` on `html` or `body`, which removes the root scrollbar and shifts the layout.

### Invoker Commands (`command` / `commandfor`)

Baseline status for Invoker commands: Newly available. It's been Baseline since 2025-12-12.
Supported by: Chrome 135 (Apr 2025), Edge 135 (Apr 2025), Firefox 144 (Oct 2025), and Safari 26.2 (Dec 2025).

If your Baseline target does not include Invoker Commands, keep the same markup and conditionally load the polyfill (the same experience, as progressive enhancement). Detect on the interface and never load it unconditionally:

```js
// MANDATORY: feature detect on HTMLButtonElement.prototype and load only when native support is missing
if (!('commandForElement' in HTMLButtonElement.prototype)) {
  import('invokers-polyfill'); // npm install invokers-polyfill
}
```

Only Rules 2 and 3 use Popover.

### Fallbacks & browser support for Popover

Baseline status for Popover: Newly available. It's been Baseline since 2025-01-27.
Supported by: Chrome 116 (Aug 2023), Edge 116 (Aug 2023), Firefox 125 (Apr 2024), Safari 17 (Sep 2023), and Safari iOS 18.3 (Jan 2025).

The Popover API is mostly **progressive enhancement**, but its defining behaviors — top-layer promotion, light-dismiss, and `popovertarget` invocation — have no CSS-only equivalent. Older browsers need a polyfill, or a manual fallback if you would rather not ship one.

**Polyfill:** To support the `popover` attribute in older browsers, conditionally load [`@oddbird/popover-polyfill`](https://github.com/oddbird/popover-polyfill). **MANDATORY:** Feature detect by checking for the `popover` property on `HTMLElement.prototype`, and load the polyfill **only** when native support is missing — do NOT load it unconditionally.

With a bundler or import map:

```js
// MANDATORY: Feature detect 'popover' on HTMLElement.prototype.
if (!Object.hasOwn(HTMLElement.prototype, "popover")) {
  import("@oddbird/popover-polyfill");
}
```

If not using a package manager, import from a CDN, e.g. `"https://unpkg.com/@oddbird/popover-polyfill@latest/dist/popover.min.js"`.

Caveats when using the polyfill:
- Do NOT use the `popover` IDL attribute for any code that may run before the polyfill is fully loaded. It will not be mirrored as an attribute, the popover will not be picked up by the polyfill, and the property will be shadowing the accessor the polyfill adds forever. Use `setAttribute()`/`removeAttribute()` instead.
- **Styling caveat:** The polyfill cannot define the real `:popover-open` pseudo-class, so it applies a `.\:popover-open` class instead. **MANDATORY:** Combine the two with `:is()` or `:where()`, otherwise browsers that lack `:popover-open` discard the entire rule:

```css
[popover]:is(:popover-open, .\:popover-open) {
  display: block;
}
```


--- Guide for responsive-table ---
# Responsive tables

Large data tables often become unreadable on small screens as columns overflow or shrink beyond legibility. This guide demonstrates how to use **sticky positioning** to keep headers visible during scrolling and how to transform the table into a mobile-friendly "stacked" layout when space is limited.

## Recommended Approach

The core of a responsive table is maintaining the relationship between data cells and their headers.

1.  **Semantic Foundation**: Use standard `<table>` elements with `<thead>`, `<tbody>`, and `<th>` elements.
2.  **Sticky Context**: Apply `position: sticky` to both column headers and row headers. This ensures that no matter how far a user scrolls in any direction, they never lose the context of what the data represents.
3.  **Adaptive Transformations**: Use `@container` queries instead of `@media` queries. This allows the table to adapt based on its own width (e.g., when placed in a sidebar or a narrow dashboard widget) rather than the entire viewport.
4.  **Label Injection**: In the stacked layout, the `<thead>` is hidden, and accessible headers are injected into each cell using `::before` pseudo-elements and CSS variables.
5.  **Legible Cells**: Keep long cell text on one line instead of letting columns shrink below legibility. See `single-line-overflow` (via `npx -y modern-web-guidance@latest retrieve "single-line-overflow"`) for techniques for truncating it and revealing the full text on demand without UX friction.

## Implementation Steps

### 1. Markup and Layout

Structure your table with standard semantic headers. Use a `.table-wrapper` to handle overflow and provide a container for queries. Add a `tabindex="0"` attribute to the container, to ensure that people using only a keyboard can consistently scroll the table.

Give the wrapper a `role="region"` attribute to communicate its purpose. Provide it with an accessible name using `aria-labelledby` (referencing the `id` attribute of an existing element that captions/names the table) or an `aria-label` attribute.

```html
<div tabindex="0" role="region" aria-labelledby="employee-table-caption" class="table-wrapper">
  <table>
    <caption id="employee-table-caption">Current employee directory</caption>
    <thead>
      <tr>
        <th>Employee</th>
        <th>Role</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <!-- Row header remains sticky horizontally on desktop, 
             and becomes a sticky card header on mobile -->
        <th>Alex Rivera</th>
        <td>Engineer</td>
        <td>Active</td>
      </tr>
    </tbody>
  </table>
</div>
```

### 2. Configure Sticky Headers
Enable scrolling and make headers sticky. Use logical properties and explicit z-index values to manage the stacking order.

```css
.table-wrapper {
  overflow: auto;
  max-inline-size: 100%;
  max-block-size: min(500px, 80vh);
  container-type: inline-size;
}

table {
  border-collapse: separate;
  border-spacing: 0;
}

/* Sticky column headers (desktop) */
thead {
  position: sticky;
  inset-block-start: 0;
  z-index: 1; /* Above sticky row headers */
}

/* Sticky row headers (desktop) */
tbody th {
  position: sticky;
  inset-inline-start: 0;
  background: white; /* Required to cover background during scroll */
}
```

### 3. Responsive Stacked Layout
When space is limited, hide the original header row and transform the table into cards. Inject labels using pseudo-elements. Only provide alternative text for non-text content, otherwise this may result in both the text content and accessible name being announced by screen readers.

```css
@container (width < 600px) {
  table, thead, tbody, tr, th, td {
    display: block;
  }

  thead {
    /* MANDATORY: Hide column header from layout and screen readers. */
    display: none
  }

  tr {
    margin-block-end: 1.5rem;
    border: 1px solid #ccc;
  }

  /* Sticky row headers at the top of each block/card */
  tbody th {
    position: sticky;
    inset-block-start: 0;
    z-index: 2;
    background: #eee;
  }

  /* Define column labels as CSS variables (often set via JS) */
  table {
    --label-1: "Employee";
    --label-2: "Role";
    --label-3: "Status";
  }

  /* Inject labels */
  td:nth-child(2)::before {
    /* MANDATORY: If using non-text content, provide the accessible name (after the /) which ensures screen readers hear the text alternative. */
    content: var(--label-2) ": ";
  }
  /* MANDATORY: Map the label for each column */
  td:nth-child(3)::before {
    content: var(--label-3) ": ";
  }
}
```


--- Guide for forms ---
# Forms

## 1. Semantic Structure and Form Element

### Guidelines

- **DO** use the `<form>` element to wrap interactive controls for data collection.
- **DO** wrap search forms and filtering controls in a `<search>` element.
- **DO** give `<form>` elements an accessible name via `aria-labelledby` (pointing to the form's heading) when a page has multiple forms.
- **DO** use `method="POST"` for sensitive data and mutations; use `method="GET"` for idempotent requests (e.g., search).
- **DO** specify the `action` attribute for the destination URL.
- **DO** specify a `name` attribute for every form control to identify data on submission.
- **DO** use semantic tags like `<button type="submit">`, `<textarea>`, `<select>`, and specific `<input>` types.
- **DO** explicitly set `type="button"` on secondary or helper buttons so they don't default to type="submit".
- **DO** use `<fieldset>` and `<legend>` (with `<legend>` as the first child) to group related controls. **DON'T** use `<fieldset>` for visual styling without a `<legend>`
- **DO** use actionable language on submit buttons (e.g., "Save changes").

- **DON'T** nest `<form>` elements inside other `<form>` elements.
- **DON'T** use `GET` for sensitive data (it exposes data in history/logs).
- **DON'T** use generic `<div>`, `<span>`, or `<a>` elements for form controls.
- **DON'T** use `type="button"` for primary submission buttons.
- **DON'T** disable textarea resizing without alternate layout provisions.
- **DON'T** use CSS to visually reorder form controls away from their DOM/keyboard `Tab` order.
- **DON'T** auto-submit a form when a user changes `<select>`, radio buttons, or checkbox without an explicit submit action.

### Code Example

```html
<search>
  <form action="/search" method="GET">
    <label for="q">Search query</label>
    <input type="search" id="q" name="q">
  
    <fieldset>
      <legend>Search filters</legend>
      <input type="checkbox" id="exact" name="exact" value="true">
      <label for="exact">Exact match only</label>
      <input type="checkbox" id="archived" name="archived" value="true">
      <label for="archived">Include archived results</label>
    </fieldset>

    <button type="submit">Search</button>
  </form>
</search>
```

### Selection Control Decision Matrix

| Options Count | Choice Type | Recommended Element | Usability & Accessibility Logic |
| :--- | :--- | :--- | :--- |
| **1** | Binary toggle (Yes/No) | `<input type="checkbox">` | **Reversible State**: Can be checked and unchecked with space unlike a radio button, which gets stuck once checked. |
| **2–5** | Single (Exclusive) | `<input type="radio">` | **Zero-click scanning**: All choices are immediately visible. Faster scan time. |
| **6+** | Single (Exclusive) | `<select>` | **Space conservation**: Use only when vertical space is premium or the list is long. |
| **10+ / Dynamic** | Single (Exclusive) | `<input list="id">` (`<datalist>`) | **Fuzzy Search**: Prevents scrolling fatigue in massive sets (e.g., countries). |
| **2+** | Multi-select | `<input type="checkbox">` | **Standard semantics**: Native non-exclusive toggles. |

**Single-Sentence Mental Model**: "Expose 2 to 5 mutually exclusive options as visible radio buttons when choices are fewer than six; use `<select>` only when space is constrained or the list is long."

## 2. Accessible Labeling and State

### Guidelines

- **DO** always associate `<label>` with its input using `for` and `id`.
- **DO** place `<label>` elements before text inputs, `<textarea>`, and `<select>` controls in the DOM and stack them visually above the control for faster scanning.
- **DO** place `<label>` elements inline immediately after `<input type="checkbox">` and `<input type="radio">` controls for consistent alignment.
- **DO** use visible labels and keep critical format instructions (e.g., `3-12 characters`) in the label or persistent helper text; do not rely on `placeholder` alone.
- **DO** ensure the vertical margin between a label and its input is less than the margin between form groups (**Gestalt Proximity Rule**).
- **DO** set `aria-invalid="true"` on form controls that fail custom validation, and clear it once resolved.
- **DO** use `aria-describedby` to link inputs with help text or error messages.
- **DO** define the `lang` attribute on `<html>` for proper device translation.
- **DO** use non-color visual cues (icons, text) to communicate state (don't rely on color alone).
- **DO** indicate clearly which fields are required both visually in the label and programmatically with the `required` attribute.
- **DO** use `aria-live` for dynamic error announcements.
  
- **DON'T** use `aria-label` when a visible `<label>` can be used or override visible text with a mismatched `aria-label`.

### Code Example

```html
<div class="field">
  <label for="username">Username: <span aria-hidden="true">*</span></label>
  <input type="text" id="username" name="username" aria-describedby="user-help" required>
  <span id="user-help" class="hint">3-12 characters.</span>
</div>

<style>
  .field {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
  margin-block-end: 1.5rem;
  }

  input:focus-visible {
    outline: 3px solid #0b57d0;
    outline-offset: 2px;
  }
</style>
```

## 3. Autofill and Input Hints

### Guidelines

- **DO** use the `autocomplete` attribute to specify expected data (e.g., `email`, `tel`, `current-password`, `new-password`).
- **DO** use `inputmode` to optimize on-screen keyboards (e.g., `inputmode="numeric"` for PINs).
- **DO** use `enterkeyhint` to set the Enter key label (e.g., `next`, `done`).
- **DO** turn off text correction on fields that hold identifiers rather than prose: `autocorrect="off"` (plus `autocapitalize="none"` and `spellcheck="false"`) on usernames, emails, URLs, codes, and search inputs. Leave the defaults on for free-text fields like messages and comments.
- **DO** use single-field inputs for complex numbers (credit cards, phones) to help autofill.
- **DO** use a single `<input type="text" inputmode="numeric" autocomplete="one-time-code">` and the WebOTP API for SMS one-time passcode verification. See guide `sms-otp-form` (via `npx -y modern-web-guidance@latest retrieve "sms-otp-form"`).

- **DON'T** use `type="number"` for credit cards, ZIP codes, or one-time passcodes (causes UI scroll issues and removes leading zeros).
- **DON'T** split a single value (such as a 6-digit OTP, phone number, or credit card) across multiple `<input>` boxes that auto-advance focus on keypress. Instead, use `type="text"` with `inputmode="numeric"` (`type=number` adds spinner buttons). If needed, styling can convey a similar UI. JS can set a `--value-length` CSS variable for higher fidelity styling that resembles these inputs, without their usability and accessibility issues.
- **DON'T** block copy-and-paste (`paste` events) or disable `autocomplete` on passwords, verification codes, or other authentication fields.

### Code Example

```html
<label for="zip">ZIP Code:</label>
<input type="text" id="zip" name="zip" autocomplete="postal-code" inputmode="numeric" pattern="\d{5}" enterkeyhint="next">

<label for="username">Username:</label>
<input type="text" id="username" name="username" autocomplete="username" autocorrect="off" autocapitalize="none" spellcheck="false" enterkeyhint="done">
```

## 4. Constraints and Validation

### Guidelines

- **DO** use native constraints: `required`, `minlength`, `maxlength`, `pattern`.
- **DO** use CSS pseudo-classes `:user-invalid` for non-intrusive styling.
- **DO** use the ValidityState API (`setCustomValidity`) for custom messaging and write clear error messages that explain how to fix the issue.
- **DO** move focus to the first invalid field (or an error summary) when a form submission fails validation.

- **DON'T** use the raw `:invalid` CSS pseudo-class alone for error styling to ensure empty required fields are not marked as invalid before the user interacts with the form.
- **DON'T** disable submit buttons to block validation; let users submit and highlight errors. However, **DO** disable the button *after* a valid submission is clicked to prevent double-posts.
- **DON'T** trigger validation errors or `aria-live` error announcements on every keystroke while the user is typing (validate on submit or `blur`, and clear errors on `input` once resolved).

### Code Example

```html
<label for="code">Activation Code (4 digits):</label>
<input type="text" id="code" name="code" required pattern="\d{4}">

<script>
  const input = document.getElementById('code');
  input.addEventListener('invalid', () => {
    input.setCustomValidity('Please enter exactly 4 digits.');
  });
  input.addEventListener('input', () => {
    input.setCustomValidity('');
  });
</script>
```

### Validation Event Timing Matrix

| Event Trigger | Phase | Action Allowed | UX / Accessibility Logic |
| :--- | :--- | :--- | :--- |
| **`input`** | Active Typing | **Clear** existing errors only. | **Non-intrusive**: Do not yell at the user before they finish typing. |
| **`blur` / `focusout`** | Exiting Field | **Run** check (if edited) and show error. | **Contextual validation**: Validate once the user indicates they are "done" with a field. |
| **`submit`** | Final Attempt | **Block** and route focus. | **Final gatekeeper**: Intercepts bad payloads and moves keyboard and screen reader focus to the first invalid field or an error summary. |

**Single-Sentence Mental Model**: "Validate on `blur` (if edited) to avoid premature warnings while typing, and reset error states on `input` as soon as the user fixes the value, and route the focus to the first error or summary on `submit`."

**Security vs UX Scale**: Client-side validation is for User Experience; Server-side validation is for Security. Never treat browser constraints as a data integrity defense.

## 5. Responsive Design and Typography

### Guidelines

- **DO** use single-column layouts for scanning.
- **DO** set `font: inherit` and `font-size: max(1rem, 1em)` on form controls to scale with larger containers while staying at least `1rem`(16px) to prevent iOS zoom.
- **DO** expand clickable areas for mobile tap targets using padding tricks.
- **DO** ensure tap targets are at least `48px`.
- **DO** use units relative to root (`rem`) and unitless `line-height`.
- **DO** use CSS logical properties (e.g., `margin-inline-start`) for RTL support.

### Code Example

```css
.form-group {
  margin-block-end: 1.5rem;
}

/* Expand clickable tap area without layout shift */
label {
  display: inline-block;
  padding: 10px 0;
  margin: -10px 0;
}

input {
  font: inherit;
  font-size: max(1rem, 1em);
  padding: 0.75rem;
  min-height: 48px;
  box-sizing: border-box;
}

@media (pointer: coarse) {
  input {
    min-height: 52px;
  }
}
```

## 6. Styling Form Controls

### Guidelines

- **DO** use `accent-color` for quick branding of native radios/checkboxes.
- **DO** use `appearance: none` for custom dropdown arrows without breaking semantics.
- **DO** ensure inputs are clearly visible with adequate border contrast (e.g., `#767676` or darker on white backgrounds).
- **DO** maintain a visible `:focus-visible` indicator on all controls. Never disable focus outlines (`outline:none`) without providing a high-contrast alternative.
- **DO** hide inputs visually using the canonical `.visually-hidden` recipe (`clip-path: inset(50%)` with 1px dimensions) — NOT `display: none`, which removes them from the accessibility tree.

### Code Example

```html
<div class="checkbox-container">
  <input type="checkbox" id="sub" name="sub" class="visually-hidden">
  <label for="sub" class="checkbox-label">Subscribe</label>
</div>

<style>
  .visually-hidden {
    position: absolute;
    clip-path: inset(50%);
    overflow: hidden;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    border: 0;
    white-space: nowrap;
  }
  .checkbox-label::before {
    content: "";
    display: inline-block;
    width: 1.25rem;
    height: 1.25rem;
    border: 2px solid #767676;
  }
  input:focus-visible + .checkbox-label::before {
    outline: 2px solid #0b57d0;
  }
</style>
```

## 7. JavaScript and AJAX

### Guidelines

- **DO** check `KeyboardEvent.isComposing` before treating the `Enter` key as a submit action in chat or text inputs to ensure IME text composition is not interrupted. See guide `ime-safe-enter-submit` (via `npx -y modern-web-guidance@latest retrieve "ime-safe-enter-submit"`).
- **DO** prevent default navigation on form submit for AJAX (`e.preventDefault()`).
- **DO** use `ValidityState` interfaces for real-time validation checks.
- **DO** announce AJAX submission results via `role="status"` or `aria-live`.
- **DO** use `aria-expanded` and `aria-controls` for dynamic UI reveals.

- **DON'T** block page submission if JS fails; ensure server-side fallback.

### Code Example

```js
form.addEventListener('submit', (e) => {
  e.preventDefault();
  const data = new FormData(form);
  // fetch('/submit', { method: 'POST', body: data });
});
```

## 8. Identity, Payments, and Advanced Security

### Guidelines

- **DO** use `autocomplete="new-password"` for sign-up and `autocomplete="current-password"` for sign-in.
- **DO** allow pasting into password fields.
- **DO** provide an accessible toggle `<button type="button">` with `aria-pressed` allowing users to unmask password input.
- **DO** indicate exact amounts on pay buttons (e.g., "Pay $100").
- **DO** use `autocomplete="cc-number"`, `cc-exp`, `cc-csc`.
- **DO** use HTTPS for all pages.
- **DO** implement cryptographically secure anti-CSRF tokens for mutating actions (POST/PUT/DELETE).
- **DO** sanitize user input (e.g., via DOMPurify) before injecting it into the DOM to prevent XSS.
- **DO** implement spam protection for open forms using accessible CAPTCHAs (e.g., invisible reCAPTCHA) or honeypot fields hidden from assistive tech (`tabindex="-1"` and `aria-hidden="true"`)

- **DON'T** utilize HTTP `GET` for endpoints executing state changes.
- **DON'T** use inline JavaScript (e.g., `onclick="..."`) directly within form markup to satisfy strict Content Security Policies (CSP).

### Code Example

```html
<form method="post">
  <input type="hidden" name="csrf_token" value="secure_token_abc123">

  <h1>Sign up</h1>

  <div class="form-group">        
    <label for="name">Full name</label>
    <input id="name" name="name" autocomplete="name" required pattern="[\p{L}\.\- ]+">
  </div>

  <div class="form-group">        
    <label for="email">Email</label>
    <input id="email" name="email" type="email" autocomplete="username" required>
  </div>

  <div class="form-group">
    <label for="password">Password</label>
    <button id="toggle-password" type="button" aria-pressed="false" aria-label="Show password" aria-describedby="toggle-warning">
      <img class="icon-eye" src="/icons/eye.svg" alt="" width="20" height="20">
      <img class="icon-eye-off" src="/icons/eye-off.svg" alt="" width="20" height="20">
    </button>
    <span id="toggle-warning" class="visually-hidden">Warning: this will display your password on the screen.</span>
    <input id="password" name="password" type="password" autocomplete="new-password" minlength="8" aria-describedby="password-constraints" required>
    <div id="password-constraints">Eight or more characters.</div>
  </div>

  <button id="sign-up" type="submit">Sign up</button>
</form>
```


## 9. Address Collection

### Guidelines

- **DO** use a single field for names.
- **DO** use `autocomplete="street-address"`.
- If the site has users in different countries, **DO** use the `<textarea>` element for addresses, to accommodate different address formats in different geographical regions. If the form uses separate inputs for address parts (e.g. Street, City), **DO** use `autocomplete` values `address-line1`, `address-line2`, etc.
- **DO** make postal codes optional.
- **DO** provide a "Same as shipping address" checkbox when collecting both shipping and billing addresses (and scope `autocomplete` with `shipping` or `billing` inside a `<fieldset>`).

- **DON'T** split name inputs into rigid variables ("First", "Last") for global audiences.
- **DON'T** enforce Latin-only characters for names and usernames.

### Code Example

```html
<!-- Accessible Address Form with Autofill -->
<form action="/save-address" method="POST">
  <div class="form-group">
    <label for="full-name">Full name</label>
    <input type="text" id="full-name" name="full_name" maxlength="100" required autocomplete="name">
  </div>

  <div class="form-group">
    <label for="address">Address</label>
    <textarea id="address" name="address" required autocomplete="street-address" maxlength="300"></textarea>
  </div>

  <button type="submit">Save Address</button>
</form>
```


## 10. Usability Testing and Analytics

### Guidelines

- **DO** test forms across multiple devices, browsers, and screen sizes.
- **DO** test keyboard-only navigation (using `Tab`, `Shift+Tab`, `Space`, `Enter`, and Arrow keys) and verify visual focus.
- **DO** emulate various impairments (visual, motor) using browser tools.
- **DO** use analytics to monitor form completion rates and bounce points.
- **DO** track discrete events (e.g., field focus, click) to find micro-friction points.

- **DON'T** rely solely on automated tools (Lighthouse) for usability; test with real users.
- **DON'T** track sensitive personal data in standard event labels.

### Code Example

```html
<form action="/submit" method="POST" id="track-form">
  <label for="postal-code">ZIP or postal code</label>
  <input type="text" id="postal-code" name="postal-code" autocomplete="postal-code" maxlength="20" required>
  <button type="submit" id="submit-btn">Submit</button>
</form>

<script>
  const trackForm = document.getElementById('track-form');
  const trackBtn = document.getElementById('submit-btn');
  
  trackBtn.addEventListener('click', () => {
    console.log('Analytics Event: Submit clicked');
  });
</script>
```

## 11. Multi-Page Forms

### Guidelines

- **DO** clearly display progress through a multi-page form with clear labels and accessible progress indicators (e.g., `aria-current="step"` or `<progress>`).
- **DO** allow users to navigate backwards and forwards between pages without losing previously entered data.
- **DO** move focus to the new step's heading (`tabindex="-1"`) or first input when transitioning between steps dynamically without a full page reload.
- **DO** use context-specific `enterkeyhint` values (e.g., `"previous"`, `"next"`) to guide navigation via on-screen keyboards.
- **DO** design layouts so that the mobile keyboard does not obscure inputs or buttons (e.g., by placing them in the upper half of the viewport when focused or using CSS scroll-padding).

- **DON'T** leave inactive wizard steps in the keyboard `Tab` order or accessibility tree (use `hidden`, `display: none`, or `inert` on non-active steps).

### Code Example

```html
<nav aria-label="Progress">
  <ol class="progress-tracker">
    <li class="step-done">Step 1: Account (completed)</li>
    <li class="step-active" aria-current="step">Step 2: Shipping</li>
    <li class="step-todo">Step 3: Payment</li>
  </ol>
</nav>

<button type="button" onclick="history.back()" enterkeyhint="previous">Previous</button>
<button type="submit" enterkeyhint="next">Next</button>
```


--- Guide for accessibility ---
# Accessibility Coding Guidelines

This guide provides actionable DOs and DON'Ts for AI coding agents to ensure web applications are accessible to all users, including those using assistive technologies.

Keep these principles in mind throughout:

- **Accessibility is the minimum, not the ceiling.** Conformance to standards is the floor; aim for genuine usability.
- **Patterns are use-case specific.** No checklist replaces real testing — including testing with disabled users — to confirm a given implementation is actually accessible in context.

Contents:

- [1. Content Navigability and Structure](#1-content-navigability-and-structure)
  - [Landmarks](#landmarks)
  - [Headings](#headings)
  - [Lists](#lists)
  - [Tables](#tables)
  - [Skip links](#skip-links)
  - [Code example: good use of landmarks, headings, lists, tables, and a skip link](#code-example-good-use-of-landmarks-headings-lists-tables-and-a-skip-link)
- [2. Semantic HTML and ARIA](#2-semantic-html-and-aria)
  - [Prefer native HTML](#prefer-native-html)
  - [ARIA roles and states](#aria-roles-and-states)
- [3. Accessible Names and Descriptions](#3-accessible-names-and-descriptions)
  - [Naming mechanisms](#naming-mechanisms)
  - [Choosing the name](#choosing-the-name)
  - [Descriptions](#descriptions)
  - [Code Example: Visually Hidden Utility](#code-example-visually-hidden-utility)
- [4. Document Metadata and Language](#4-document-metadata-and-language)
  - [Language](#language)
  - [Titles](#titles)
  - [Iframes](#iframes)
  - [Code Example: using the `<title>` and `<iframe>` elements](#code-example-using-the-title-and-iframe-elements)
- [5. Keyboard and Focus Management](#5-keyboard-and-focus-management)
  - [Tab order and focusability](#tab-order-and-focusability)
  - [Keyboard handlers](#keyboard-handlers)
  - [Focus indicators](#focus-indicators)
  - [Target sizes](#target-sizes)
- [6. Alternate Text and Media](#6-alternate-text-and-media)
  - [Images](#images)
  - [Inline SVGs](#inline-svgs)
  - [Complex images and charts](#complex-images-and-charts)
  - [Audio and video](#audio-and-video)
  - [CSS generated content](#css-generated-content)
  - [Content Visibility Decision Matrix](#content-visibility-decision-matrix)
- [7. Forms and Input Controls](#7-forms-and-input-controls)
  - [Labels and hints](#labels-and-hints)
  - [Input assistance and validation](#input-assistance-and-validation)
- [8. Live Regions](#8-live-regions)
  - [Live Region Urgency Table](#live-region-urgency-table)
  - [When to announce](#when-to-announce-live-regions)
  - [Managing announcements](#managing-announcements)
- [9. Color](#9-color)
- [10. Typography](#10-typography)
- [11. Motion and Preferences](#11-motion-and-preferences)
- [12. Modals and Native Dialogs](#12-modals-and-native-dialogs)
  - [Native `<dialog>`](#native-dialog)
  - [Custom overlays](#custom-overlays)
- [13. Testing Validations](#13-testing-validations)
  - [Automated checks](#automated-checks)
  - [Manual testing](#manual-testing)

## 1. Content Navigability and Structure

### Landmarks

- **Place all content within landmarks:** Wrap each relevant part of the page in `<header>`, `<nav>`, `<main>`, `<aside>`, and `<footer>` elements so assistive-tech users can jump between regions. (1.3.6 Identify Purpose (Level AAA))
- **Use the correct landmark:** Use the `<header>` element as a container for introductory content, the `<nav>` element as a container for site-wide or in-page navigation links, the `<main>` element as a container for the main content of the page, the `<aside>` element as a container for content that is tangentially related to the main content, and the `<footer>` element as a container for information about the related content, such as the author, copyright information, and links to related documents. (1.3.1 Info and Relationships (Level A))
- **Use one `<main>` landmark per page:** Avoid using multiple `<main>` elements on a single page. (1.3.1 Info and Relationships (Level A))
- **Provide distinguishable accessible names for navigation regions:** If a page contains multiple `<nav>` elements, apply the `aria-label` attribute to each element and set its value to a distinguishable accessible name for the region. For example: `<nav aria-label="Primary">`, `<nav aria-label="Secondary">`, and so on. (Best practice)
- **Don't overuse landmarks:** Too many landmarks dilute their value. In particular, avoid labeling a `<section>` (which turns it into a `region` landmark) — `region` should be a last resort when no other landmark fits. (Best practice)

### Headings

- **Structure main content with headings:** Use `<h1>`–`<h6>` elements sequentially so screen reader users get a navigable outline. (1.3.1 Info and Relationships (Level A))
- **Mandatory - Don't use "fake" headings:** Never use `<div>` or `<span>` elements to look like headings without standard `<h1>`–`<h6>` elements. (1.3.1 Info and Relationships (Level A))
- **Avoid nesting headings incorrectly:** Make sure that, if a sub-heading is visually less important than its parent heading, its heading level is lower in the heading hierarchy. (1.3.1 Info and Relationships (Level A))
- **Use one `<h1>` element per page:** Use the `<h1>` element for the page's main heading. Having more than one `<h1>` element on a page makes it difficult for screen reader users to identify the actual main heading. (Best Practice)
  - **Caveat:** If a page includes a modal dialog that is marked up using the `<dialog>` element, `role="dialog"`, or `role="alertdialog"`, it is fine to mark up its main heading using the `<h1>` element because the dialog is a new window that is separate from the page.
- **Avoid "skipped" heading levels:** Avoid jumping directly from (for example) `<h1>` → `<h4>` to avoid breaking the logical hierarchy. (Best Practice)
- **Avoid placing headings inside the `<summary>` element:** Some browsers still expose this element as a button, which removes all roles from its children including headings. If a heading must act as a disclosure trigger, use an accordion or a disclosure implemented with ARIA where the heading element wraps the button, rather than use the `<details>` and `<summary>` elements. (Best Practice)

### Lists

- **Use lists for repeated, contiguous content:** `<ul>`/`<ol>` give assistive tech a count of listitems up front and let users skip the entire list. (1.3.1 Info and Relationships (Level A))
- **Use the correct list element:** Use the `<ul>` element for unordered lists where the order of the items is **not** important (such as a list of related products), and use the `<ol>` element for ordered lists where the order of the content **is** important (such as a list of instructions). (1.3.1 Info and Relationships (Level A))
- **Don't use lists for non-list content:** Do not use list markup to mark up separate paragraphs of text, as screen readers will announce list information when they encounter lists, therefore leading to a screen reader hearing potentially confusing and redundant information about the related content. (1.3.1 Info and Relationships (Level A))
- **Don't use lists for checkboxes and radio buttons:** When marked up correctly, screen readers will already announce the number of checkboxes or radio buttons, as well as the number of the currently focused checkbox / radio button in the set, even though there is no list markup. Additional list markup will lead to duplication. (1.3.1 Info and Relationships (Level A))

### Tables

- **Do use the correct table elements:** Use the `<table>` element to identify the table, the `<caption>` element to provide a title and accessible name for the description, the `<tr>` element to identify individual rows in the table, and the `<th>` and `<td>` elements to identify header and data cells respectively. (1.3.1 Info and Relationships (Level A))
- **Do use the `scope` attribute on `<th>` elements:** The `scope` attribute indicates whether the `<th>` element represents a row header (`<th scope="row">`) or a column header (`<th scope="col">`). (1.3.1 Info and Relationships (Level A))
- **Mandatory - Don't use tables for layout:** Screen readers will announce redundant information about the layout, which may be confusing for screen reader users, while the use of tabular markup has an impact on the reading and keyboard focus order of content. Use CSS Grid/Flexbox for visual layouts instead. (1.3.1 Info and Relationships (Level A))
- **Avoid overly-complex tables:** Spanned rows, spanned columns, nested tables, and expandable / collapsible rows can make sense visually and meet the related WCAG success criterion, but the overall structure can be disorienting and difficult to navigate for screen reader users. In such cases, break tables up into smaller tables that are easier and more efficient to navigate. (Best Practice)

### Skip links

- **Provide skip links** prior to repeated content like site headers with navigation or long/infinite lists, so that keyboard users can easily bypass them. (2.4.1 Bypass Blocks (Level A))
  - **Caveat:** Sometimes screen magnifiers do not follow the focus when a skip link’s target is not normally focusable.
    The recommended workaround is to make the target programmatically focusable, but not a part of the tab order, using `tabindex="-1"`.
    If the target contains focusable elements, this creates another usability issue as clicking within the target will always set the **sequential focus navigation start point** to the target rather than at a point between focusable elements.
    A solution that satisfies both user expectations is to make the first meaningful element within the intended target the actual target of the skip link with `tabindex="-1"`, for example a heading (`<h1 id="content" tabindex="-1">`).
    Beware that any content prior to such an element will be skipped, including other relevant content within the targeted section, and this creates usability gaps for other assistive tech users.
- **Avoid using skip links where they are not needed:** A set of pages whose only common element is a single link to the Home page does not need a skip link. (Best Practice)
- **Avoid overusing skip links:** A single skip link, or two skip links to cover the primary and secondary sets of common navigation links, is usually sufficient on a single page. Multiple unnecessary skip links add to the number of <kbd>Tab</kbd> stops to a page, which causes frustration for people who use the keyboard alone for navigation. (Best Practice)

```html
<!-- Good: Skip to main content -->
<a href="#content" class="skip-link">Skip to main content</a>
<main id="content">...</main>
```

### Code Example: good use of landmarks, headings, lists, tables, and a skip link

```html
<!-- Good: Semantic landmarks, heading hierarchy, skip link -->
<header>
  <a href="#platform-dashboard" class="skip-link visually-hidden">Skip to content</a>
  <nav aria-label="Primary">
    <ul>
      <li><a href="/">Home</a></li>
    </ul>
  </nav>
</header>
<main>
  <h1 id="platform-dashboard" tabindex="-1">Platform Dashboard</h1>
  <section>
    <h2>User Statistics</h2>
    <table>
      <caption>Monthly active users</caption>
      <thead>
        <tr>
          <th scope="col">Month</th>
          <th scope="col">Users</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>January</td>
          <td>12,000</td>
        </tr>
      </tbody>
    </table>
    <h3>Notes</h3>
    <ul>
      <li>Results do not include users without active subscriptions</li>
      <li>Results are accurate as of 31 December 2025</li>
    </ul>
  </section>
</main>
```

## 2. Semantic HTML and ARIA

### Prefer native HTML

- **Prefer HTML elements and attributes to ARIA:** Avoid `<div role="button">` or `<a role="button">` and use `<button>` instead. Native HTML elements and attributes already have the correct role and behavior, including keyboard support, built-in by default. `<button>` already implies `role="button"`, `required` already implies `aria-required`, and no additional JavaScript is required to ensure the correct role and behavior is supported. (Best Practice)
  - **Caveat:** ARIA is required when the related feature is not available in HTML, for example there are no HTML elements explicitly intended for building a tabbed navigation widget, but ARIA includes appropriate role and state properties for this purpose.
- **Don't add redundant ARIA roles or properties:** Avoid `<ul role="list">`, `<nav role="navigation">`, and `<input required aria-required="true">`. (Best Practice)
  - **Caveat:** Safari removes list semantics from `<ul>`/`<ol>` outside `<nav>` when `list-style: none` or `display: flex`/`grid` is applied. In that case `role="list"` is required to restore them.
- **Don't apply interactive ARIA roles to structural HTML elements:** Use `<li><span role="button">Button in a list</span></li>`, not `<li role="button">Button in a list</li>`, to avoid breaking the container list semantics. (4.1.2 Name, Role, Value (Level A))
  - **Caveat:** It is acceptable to apply ARIA roles to structural HTML elements that have similar semantics, for example a tree view: `<ul role="tree"><li role="treeitem">…</li>…</ul>`.

### ARIA roles and states

- **Match ARIA implementations to actual behavior:** When applying `role="tab"` to an element, it must then behave like a tab — including keyboard interactions. Many ARIA patterns can't be implemented in CSS alone and need JavaScript. (4.1.2 Name, Role, Value (Level A))
- **Manage toggle states:** Utilize `aria-expanded` and `aria-pressed` to communicate toggle states for custom controls. (4.1.2 Name, Role, Value (Level A))
- **Be deliberate about `disabled` vs `aria-disabled`:** `disabled` removes the element from the focus order entirely (and `tabindex="0"` won't bring it back), which is often wrong for toolbar buttons or links. `aria-disabled="true"` keeps the element focusable so users can land on it and learn it's disabled, but because it only communicates state to assistive technologies, you must also prevent activation (such as pointer clicks and keyboard triggers) in JavaScript. (4.1.2 Name, Role, Value (Level A))
- **Mandatory - Don't hide interactive elements from screen readers:** Do not apply `aria-hidden="true"` to interactive elements that receive focus, or to their parent elements. (4.1.2 Name, Role, Value (Level A))
- **Mandatory - Don't suppress the roles of interactive elements:** Applying `role="presentation"` or `role="none"` to an interactive element strips its semantics. The element will still be exposed to assistive technologies and announced by screen readers, but its role and any state information will not be, which results in confusion and potentially unexpected behavior. (4.1.2 Name, Role, Value (Level A))
- **Don't assume custom elements have no ARIA:** Custom elements can attach ARIA via `ElementInternals`, which some automated test tools can't see — so the absence of `role`/`aria-*` attributes in markup doesn't prove the element has no semantics. Verify with the browser's accessibility-tree inspector. (Best Practice)

## 3. Accessible Names and Descriptions

Every interactive element and some landmarks need an accessible name, and many benefit from an accessible description. Names are short and identify the element; descriptions add context.

### Naming mechanisms

- **Prefer native naming mechanisms:** `<label>` for form controls, `<caption>` for `<table>`, `<legend>` for `<fieldset>`, `<figcaption>` for `<figure>`. (Best Practice)
- **Explicitly associate `<label>` with its control via `for`/`id`:** As well as ensuring the control is appropriately labeled by the contents of the `<label>` element, this results in a larger target area for people to activate the label _or_ its related control to move focus to the control, which isn't globally supported with other forms of labeling (such as using the `aria-labelledby` attribute). Additionally, some assistive technologies, particularly voice recognition software, require the `for`/`id` relationship to be explicitly set, even if an equivalent accessibility-supported approach (such as nesting an `<input>` inside a `<label>`) is taken. (4.1.2 Name, Role, Value (Level A))
- **Prefer `aria-labelledby` over `aria-label` when a visible label exists:** This avoids duplication, improves maintainability, and translates better. (Best Practice)
- **Don't use `title` as a naming mechanism:** The value of this attribute is only displayed on mouse hover, and cannot be displayed or otherwise accessed using the keyboard in any browser. (Best Practice)
  - **Caveat:** `<iframe>` is an exception, as the `title` attribute is the standard way of providing an accessible name for this element.
- **Don't use `placeholder` as a naming mechanism:** While the value of this attribute is initially displayed inside an `<input>` or `<textarea>`, it disappears as soon as the user enters text into the field, meaning that there is no longer a visual cue as to what the field represents. The contrast between `placeholder` text and its background in most browsers is very low, and therefore is difficult for people to perceive. (3.3.2 Labels or Instructions (Level A))
- **Don't put `aria-label`/`aria-labelledby` on elements that shouldn't be named:** Examples include plain `<div>`, `<span>`, and other custom elements without a role. These attributes are only intended for providing accessible names for elements that have explicit or implicit widget (for example, button, link, and tab), landmark, image, or iframe roles. (1.3.1 Info and Relationships (Level A))
  - **Caveat:** Custom elements may have an implicit role set via `ElementInternals`, so the absence of a `role` attribute isn't conclusive.

### Choosing the name

- **Avoid inconsistent link text:** If multiple hyperlinks direct users to the same target page, make sure each link has the same accessible name, which should typically be the same as its visible link text. For example, if the target page for a link is `profile.html`, make sure that all links have an accessible name of "My Profile" **or** "Profile"; do not use "My Profile" in one instance, and "Profile" in the other. (Best Practice)
- **Disambiguate controls that look visually identical but which perform different actions by their accessible name:** For example, a page may include multiple "Edit" buttons, each of which triggers functionality to perform a different action, such as edit the user's name, edit the user's password, and edit the user's address. While it may be visually obvious from the surrounding content what the purpose of these buttons might be, screen reader users may only hear "Edit, button". Techniques to resolve this include the following: (4.1.2 Name, Role, Value (Level A))
  - **Use visually hidden text:** The text is included in the DOM but is visually hidden using CSS. For example `<button>Edit <span class="visually-hidden">first name</span></button>`. Refer to the [code example: visually hidden utility](#code-example-visually-hidden-utility) for the full CSS.
  - **Apply the `aria-label` attribute to the control:** The value of this attribute should then include the visible text as well as important contextual information, for example `<button aria-label="Edit name">Edit</button>`, `<button aria-label="Edit address">Edit</button>`, and so on.
  - **Use the `aria-labelledby` or `aria-describedby` attribute to associate the control with the content it relates to:** Chaining IDs in `aria-labelledby` appends the related text to the control's accessible name (for example, `<p id="firstName">First name</p> <button id="editFirstName" aria-labelledby="editFirstName firstName">Edit</button>`), whereas `aria-describedby` provides the context as an accessible description (`<p id="firstName">First name</p> <button aria-describedby="firstName">Edit</button>`).
- **Do include a control's visible text in its accessible name:** Any visible text used to label a control must be included exactly as written in the control's accessible name. The accessible name can include additional information before or after the visible text, but the visible text itself must not differ. For example, the accessible name for a link containing the link phrase "Read more" can be "Read more about [subject]", because the visible text is included without modification. However, the accessible name cannot be "Read some more about [subject]", because the term "some" appears between the words "Read" and "more", which is not reflected in the visible text. (2.5.3 Label in Name (Level A))
- **Don't reuse an accessible name across controls with different effects in the same view:** Make sure that each accessible name is disambiguated. (4.1.2 Name, Role, Value (Level A))
  - **Caveat:** Having two separate buttons with the accessible name of "Close" in two separate dialog boxes is fine, because only one dialog box is reachable at a time; however, multiple "Edit" buttons for different effects in the same dialog box is not.
- **Don't reuse an accessible name across hyperlinks that point to different `href` targets:** For example, avoid `<a href="annualreport2025.html">Annual Report</a>` and `<a href="annualreport2026.html">Annual Report</a>`. Use `<a href="annualreport2025.html">Annual Report 2025</a>` and `<a href="annualreport2026.html">Annual Report 2026</a>` (or an equivalent technique for disambiguating controls) instead.
- **Don't pack descriptions, error messages, or instructions into the label:** Verbose labels confuse and frustrate people who use screen readers. Instead, use the `aria-describedby` attribute to programmatically associate any additional content with the field. For example: `<label for="yourComments">Your comments</label><p id="yourCommentsWarning">Please do not include any personal information in this field.</p><textarea id="yourComments" aria-describedby="yourCommentsWarning"></textarea>`. Screen readers will then announce the label first, followed by the control type, and only then announce additional information that a user can skip if they are already aware of it. (Best Practice)
- **Don't repeat state information already exposed by ARIA inside the label:** Examples include information exposed via the `aria-expanded`, `aria-checked`, `aria-selected`, `aria-pressed`, and similar attributes. This creates duplication, redundancy, and ambiguity. (Best Practice)
- **Don't include the role name in the label:** This will lead to duplication. For example, `<nav aria-label="Primary navigation">` will be read by screen readers as "Primary navigation, navigation". (Best Practice)

### Descriptions

- **Identify instructions, error messages, and any other important information explicitly related to a control as a description:** Examples of descriptions include: (1.3.1 Info and Relationships (Level A))
  - A list of password requirements when creating an account
  - An error message related to a field in a previously submitted form
  - Additional instructions, such as "You must agree to the terms and conditions before you can submit the form"
- **Make sure the description is available to assistive technologies when the related element receives focus:** Take one of the following approaches (1.3.1 Info and Relationships (Level A)):
  - If the description is already visible on the page, programmatically associate it with the element using the `aria-describedby` attribute.
  - If the description is not visible on the page and is explicitly for screen reader users (in other words, when providing a visible description is not appropriate or useful), apply the `aria-description` attribute to the element and use it to provide an appropriate description.
- **Avoid including a description for every element:** if the primary label already provides sufficient information (such as "First name"), any additional description is likely to be redundant. (Best Practice)
  - **Caveat:** Inline error messages associated with controls, such as error messages below / above text fields, as well as secondary labels that should be announced when the element receives focus, are exceptions.
- **Avoid including information in the description that is already provided by attributes applied to the element:** For example, including "This is a required field" as a description for an `<input>` element that already includes the `required` attribute will lead to duplicate announcements. (Best Practice)
  - **Caveat:** `aria-invalid="true"` is an exception; many screen readers announce "invalid" when they reach an `<input>` that includes this attribute set to `true`, which indicates that the field is in error. However, it does not indicate what the error is. In such cases, a description (the actual human readable error message) is required. This attribute should only be applied and set to true when the error message is present.
- **Avoid including interactive elements in an `aria-describedby` target** unless the content of the element reads sensibly as a description on its own. For example: (Best Practice)
  - This is acceptable, as the entire text string makes sense when announced: `<p id="description">I understand the <a href="tandc.html">terms and conditions</a>.</p>`
  - This is not appropriate, as the description will be announced as "Please don't include personal information in this field. Learn more.", where "Learn more" will be announced out of its intended context: `<p id="description">Please don't include personal information in this field. <a href="…">Learn more</a></p>`. Instead, only include the plain text in the referenced description: `<p><span id="description">Please don't include personal information in this field.</span> <a href="…">Learn more</a></p>`.

### Code Example: Visually Hidden Utility

A `.visually-hidden` utility provides text for screen readers without rendering it visually. It's commonly used for skip links, additional context on icon-only buttons, and supplementary labels.

```css
/* Hides content visually but keeps it in the accessibility tree.
   :focus-within / :active opt elements out — useful for skip links and
   any focusable content wrapped in this class. */
.visually-hidden:where(:not(:focus-within, :active)) {
  position: absolute !important;
  clip-path: inset(50%) !important;
  overflow: hidden !important;
  width: 1px !important;
  height: 1px !important;
  margin: -1px !important;
  padding: 0 !important;
  border: 0 !important;
  white-space: nowrap !important;
}
```

When the hidden content is focusable (skip links, focus-receiving wrappers), the `:focus-within`/`:active` exception lets it become visible. Style the visible state per situation, e.g. a skip link to the main content typically wants fixed positioning at the top-left of the viewport so the rest of the page doesn't shift.

## 4. Document Metadata and Language

### Language

- **Do declare the page's human language:** Always apply the `lang` attribute to the page's `<html>` element, and always set it to the primary human language of the page's content. For example, `<html lang="en">`. (3.1.1 Language of Page (Level A))
- **Do declare changes in the page's human language:** If there is a language change on the page, apply the `lang` attribute to the parent/container element for the affected content, and set the value of this attribute to the shortcode for the language of the affected content. For example: `<p>In Germany, you may be greeted by someone saying <span lang="de">Guten Morgen</span>.</p>`. (3.1.2 Language of Parts (Level AA))
- **Don't set the value of the `lang` attribute to a value that doesn't match the human language of the content:** This causes screen readers and other text-to-speech software to announce the content in a non-understandable manner. (3.1.1 Language of Page (Level A), 3.1.2 Language of Parts (Level AA))

### Titles

- **Do include the `<title>` element in the `<head>` section for all pages:** This includes pages embedded into a document using an `<iframe>`. (2.4.2 Page Titled (Level A))
- **Provide unique page titles:** Every page should have its own title that unambiguously reflects the page's purpose or content. (2.4.2 Page Titled (Level A))
- **Front-load the page's `<title>` with unique content:** For example, `<title>Page Topic | Site Name</title>`. (Best Practice)
- **Update single-page application (SPA) titles during page transitions:** For example, if the page title is `<title>Contact Us</title>` when a contact form is displayed, update the title to `<title>Thank you for contacting us!</title>` when the form is successfully submitted. (2.4.2 Page Titled (Level A))
- **Don't include an empty `<title>` element in the `<head>` section of a page:** No matter how short or inconsequential a page appears, do not use `<title></title>`. Page titles appear in the browser tab, so pages are distinguishable when users have multiple tabs open, and are typically announced by screen readers when the page is opened. (2.4.2 Page Titled (Level A))
- **Avoid using the same title for multiple pages, or using ambiguous page titles:** In such cases, pages are indistinguishable without reviewing the actual page content itself. (2.4.2 Page Titled (Level A))

### Iframes

- **Do provide a descriptive `title` for `<iframe>` elements:** All `<iframe>` elements should include a `title` attribute set to a value that unambiguously describes the contents of the `<iframe>`. (4.1.2 Name, Role, Value (Level A))
- **Don't disable iframe scrolling** using `scrolling="no"` (deprecated) or `overflow: hidden` on iframes. Users who zoom in or enlarge text need to scroll to reach content that overflows. (1.4.4 Resize Text (Level AA), 1.4.10 Reflow (Level AA))

### Code Example: using the `<title>` and `<iframe>` elements

```html
<!-- Good: Distinct title and language declaration -->
<html lang="en">
<head>
  <title>Analytics Reports | Guidance Platform</title>
</head>
<body>
  <p>The motto is <span lang="la">"Carpe diem"</span>.</p>
  <iframe title="Interactive Sales Chart" src="/chart"></iframe>
</body>
</html>
```

## 5. Keyboard and Focus Management

### Tab order and focusability

- **Provide a logical tab order:** Make sure that the order in which elements receive focus follows an appropriate sequence. (2.4.3 Focus Order (Level A))
  - **Caveat:** In left-to-right reading languages, the tab order is logical when focus moves from top-to-bottom and left-to-right. However, in right-to-left reading languages, the tab order is logical when focus moves from top-to-bottom and right-to-left.
- **Use `tabindex` only when necessary:** Apply `tabindex="0"` to elements requiring focus where an appropriate interactive role has been applied but the element isn't focusable by default; for example, `<span role="button" tabindex="0">Print</span>` (2.4.3 Focus Order (Level A))
- **Manage focus correctly to and from updated content:** For example, if a dialog box appears on the page, make sure that focus immediately moves to the dialog box, is restricted to the contents of the dialog box, and (when dismissed) returns to the element that originally triggered the dialog box. (2.4.3 Focus Order (Level A))
- **Don't apply `tabindex="0"` to interactive elements that are already focusable by default:** Native elements like the `<button>`, `<a>` (only with the associated `href` attribute), and `<input>` elements are already keyboard focusable, and therefore do not require `tabindex="0"`. (2.4.3 Focus Order (Level A))
- **Don't apply `tabindex="0"` to static, non-interactive, and hidden elements:** Only elements that (when activated) perform a specific action should be included in a page's tab order. Static, non-interactive, and hidden elements (whether hidden temporarily or permanently) must not be focusable. (2.4.3 Focus Order (Level A))
- **Mandatory - Don't use positive `tabindex` values:** Never apply `tabindex="1"` (or any value > 0) to elements, as doing so imposes a tab order on the page that bears no resemblance to the intended or expected tab order. (2.4.3 Focus Order (Level A))

### Keyboard handlers

- **Attach <kbd>Enter</kbd>/<kbd>Space</kbd> handlers for custom simulated interactive elements:** When implementing a custom keyboard handler for button-like elements, <kbd>Enter</kbd> should be a `keydown` handler and <kbd>Space</kbd> should be a `keyup` handler (matching native `<button>` behavior where <kbd>Enter</kbd> repeats and <kbd>Space</kbd> triggers on release). (2.1.1 Keyboard (Level A))
- **Don't attach keyboard handlers to native interactive elements:** Native elements such as the `<button>`, `<input>`, and `<a>` (with the required `href` attribute) elements already support the <kbd>Enter</kbd> and (except for the `<a>` element) the <kbd>Space</kbd> keys by default, so adding these keyboard handlers is redundant. (Best Practice)
  - **Caveat:** if the `<a>` element is repurposed as a button through the inclusion of `role="button"`, a `keyup` handler is still required to support the <kbd>Space</kbd> key to match native `<button>` behavior.

#### Code Example: Keyboard handlers

```javascript
// Good: Keyboard handlers for complex custom widgets (e.g., Tree items, tabs).
// NOTE: This pattern applies ONLY to non-standard UI where no native HTML tag exists.
// Always prioritize native <button> or <input> elements for standard interactions.
// Elements MUST have the appropriate ARIA role (e.g., role="treeitem" or role="tab").
customWidget.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    toggleWidgetState();
  }
  if (e.key === ' ') {
    e.preventDefault(); // Prevent page scrolling on Spacebar keydown
  }
});

customWidget.addEventListener('keyup', (e) => {
  if (e.key === ' ') {
    toggleWidgetState();
  }
});

function toggleWidgetState() {
  // E.g., Manage toggle/expanded states for custom controls
  const isExpanded = customWidget.getAttribute('aria-expanded') === 'true';
  customWidget.setAttribute('aria-expanded', !isExpanded);
}
```

### Focus indicators

- **Use `:focus-visible` when styling focus indicators:** When defining custom focus indicators, always style the `:focus-visible` state (not `:focus`) explicitly. (Best Practice)
- **Prefer browser native focus indicators over custom focus indicators:** Leave focus indication to the browser unless custom focus styling is needed to meet contrast or design requirements. (Best Practice)
- **Mandatory - Don't disable browser native focus indicators without providing a replacement custom focus indicator:** When using `outline: none;` to suppress the browser native focus indicator, provide an equivalent custom focus indicator that has a contrast ratio of at least `3:1` against adjacent content (2.4.7 Focus Visible (Level AA), 1.4.11 Non-text Contrast (Level AA)).
- **Prefer `outline` over other properties for focus rings:** If `box-shadow` must be relied on for focus rings, provide an `outline`-based fallback for High Contrast Mode using the `forced-colors` media query. (Best Practice)
- **Pair custom focus outlines with `outline-offset`:** This visually separates the ring from the element. (Best Practice)

#### Code Example: Custom focus indication

```css
/* Good: High contrast focus border */
:where(a:any-link, button):focus-visible {
  outline: 3px solid #ff0055;
  outline-offset: 3px;
}
```

### Target sizes

- **Do size interactive elements to have a target of at least 24x24 CSS pixels:** Enforce the target size of elements using `min-block-size` / `min-inline-size` or through padding rather than `width` / `height` so that content grows the target but not shrink it. (2.5.8 Target Size (Minimum) (Level AA))
  - **Caveat:** Interactive elements _may_ have a target of less than 24x24 CSS pixels _as long as_ they are positioned in such a way that if a 24 CSS pixel diameter circle is centered on the bounding box of each element, the circles do not intersect nearby targets or circles for other targets that are less than 24x24 CSS pixels.
- **Bump targets up on coarse pointers:** `@media (pointer: coarse) { … }`. (2.5.8 Target Size (Minimum) (Level AA))
- **Don't use `touch-action: none;` for custom gestures:** This disables page scrolling through the element. Scope to the axis you actually need - `pan-y` for horizontal swipes (the page still scrolls vertically), and `pan-x` for vertical swipes. Reserve `none` for elements where no native touch behavior makes sense, such as a drawing canvas. (2.1.1 Keyboard (Level A))

## 6. Alternate Text and Media

### Images

- **Mandatory - Apply the `alt` attribute to all `<img>` elements:** browsers replace the image with the value of this attribute for people who use screen readers. (1.1.1 Non-text Content (Level A))
- **Do provide informative visual descriptions:** Describe the purpose of the image (for example, "Search", not "Magnifying glass"). (1.1.1 Non-text Content (Level A))
- **Do apply `alt=""` to decorative visuals:** This prevents screen readers from announcing them. (1.1.1 Non-text Content (Level A))
- **Don't use clichéd prefixes:** Avoid terms like "Image of…" and "Picture of…". (Best Practice)
- **Don't use underscores in filenames:** Use dashes if the filename might be announced as fallback. (Best Practice)

#### Code Example: Providing a text description for `<img>` elements

```html
<!-- Decorative -->
<img src="divider.png" alt="">

<!-- Informative (Functional) -->
<a href="/search">
  <img src="glass.png" alt="Search the platform">
</a>
```

### Inline SVGs

- **Do apply `role="img"` to the `<svg>` element for non-decorative SVGs:** This is so that they are globally exposed as images. (4.1.2 Name, Role, Value (Level A))
- **Do provide a text description for non-decorative SVGs:** Use one of the following techniques: (1.1.1 Non-text Content (Level A))
  - Include a nested `<title>` element as a child of the `<svg>` element that includes the text description. **or**
  - Apply the `aria-label` attribute to the `<svg>` element and set its value to an appropriate text description.
- **Do hide decorative SVGs from assistive technologies:** Apply `aria-hidden="true"` to decorative `<svg>` elements to prevent screen readers from announcing them. (1.1.1 Non-text Content (Level A))

#### Code Example: Providing a text description for non-decorative SVGs using the `<title>` element

```html
<!-- Inline non-decorative SVG: example that uses the <title> element -->
<svg role="img" viewBox="0 0 24 24">
  <title>Home</title>
  <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
</svg>
```

#### Code Example: Providing a text description for non-decorative SVGs using the `aria-label` attribute

```html
<!-- Inline non-decorative SVG: example that uses the aria-label attribute -->
<svg role="img" viewBox="0 0 24 24" aria-label="Home">
  <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
</svg>
```

#### Code Example: Identifying decorative SVGs

```html
<!-- Inline Decorative SVG (hide from assistive technologies) -->
<svg aria-hidden="true" viewBox="0 0 24 24">
  <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
</svg>
```

### Complex images and charts

- **Provide long descriptions for complex images:** Use `<figure>`/`<figcaption>` or `aria-describedby` for charts and infographics. (1.1.1 Non-text Content (Level A))
- **Provide semantic data tables as alternatives:** Provide semantic data tables as accessible alternatives for charts and other complex visualizations. (1.1.1 Non-text Content (Level A))

#### Code Example: Complex graph with figcaption

```html
<!-- Complex graph with figcaption -->
<figure>
  <img src="chart.png" alt="Sales growth graph 2024.">
  <figcaption>Sales grew 20% in Q3 due to new platform launch.</figcaption>
</figure>
```

### Audio and video

- **Mandatory - Provide a transcript for audio-only content and combined video & audio content:** The transcript should be verbatim, and include all of the dialogue as well as text descriptions of important non-speech sounds such as sound effects. (1.2.1 Audio-only and Video-only (Prerecorded) (Level A), 1.2.3 Audio Description or Media Alternative (Prerecorded) (Level AA))
- **Mandatory - Provide a text description or an audio track for video-only content:** Examples include text-based instructions for an animation on how to use a particular product, and a separate audio track that includes a description of the action in the video. (1.2.1 Audio-only and Video-only (Prerecorded) (Level A))
- **Mandatory - Provide synchronous captions for videos:** Supply WebVTT captions for audio tracks within video content. The captions should be verbatim and synchronous with the audio track, and include all of the dialogue as well as meaningful non-speech content such as sound effects and other important information conveyed within the soundtrack (for example, "Ominous music plays"). (1.2.2 Captions (Prerecorded) (Level A))
  - **Caveat:** Captions are not required if the video is a decorative alternative for text that is already present and is clearly identified as such.
- **Do provide an audio description for videos:** Include an additional audio track within the video that augments the visual content displayed on-screen. The audio description should convey information about the scene that is not described or spoken in the main audio track, and should be conveyed during existing pauses in the dialogue. (1.2.3 Audio Description or Media Alternative (Prerecorded) (Level A), 1.2.5 Audio Description (Prerecorded) (Level AA))

#### Code Example: Video and audio content with captions and transcript

```html
<!-- Video with Captions tracks -->
<video controls>
  <source src="intro.mp4" type="video/mp4">
  <track src="caps.vtt" kind="captions" srclang="en" label="English">
</video>

<!-- Audio with expandable transcript details -->
<audio controls src="podcast.mp3" aria-details="podcast-transcript"></audio>
<details id="podcast-transcript">
  <summary>View Transcript</summary>
  <div class="transcript-content">
    Welcome to the show...
  </div>
</details>
```

### CSS generated content

- **Alt text for CSS generated content:** Use the alternative text argument of `content` (e.g. `content: url(icon.svg) / "Save";`) and keep meaningful text in the DOM. See `accessible-generated-content` (via `npx -y modern-web-guidance@latest retrieve "accessible-generated-content"`) for more details. (1.1.1 Non-text Content (Level A))

### Content Visibility Decision Matrix

| Intent | Visual | Screen Reader | Focusable | Structural Pattern |
| :--- | :--- | :--- | :--- | :--- |
| **Visible to all** | Yes | Yes | Yes | Standard rendering |
| **Screen Reader only** | No | Yes | Yes (if interactive) | Visually hidden utility (e.g. `.visually-hidden`) |
| **Visual only** | Yes | No | No | `aria-hidden="true"` |
| **Hidden for all** | No | No | No | `hidden` attribute / `display: none` |

**Heuristic Rule:** If an element can receive keyboard focus, it must not be hidden via `aria-hidden="true"`.

**Note:** only use screen reader only content as a last resort. If content is important, it should be visible for everyone.

## 7. Forms and Input Controls

### Labels and hints

- **Mandatory - Provide a label for all form controls:** Do not rely on the currently selected input or value as a way of labeling the control. (3.3.2 Labels or Instructions (Level A))
- **Connect Labels Programmatically:** Use `<label for="id">` linked to `<input id="id">`. (1.3.1 Info and Relationships (Level A))
- **Don't use placeholders as primary labels:** Placeholders are not persistent labels. Only use placeholders to provide  brief hints, such as an example of an appropriate input. (3.3.2 Labels or Instructions (Level A))
- **Link hints to inputs via `aria-describedby`:** Associate help text with inputs, and place the hint above the input so autocomplete popovers don't cover it during editing. (1.3.1 Info and Relationships (Level A))

#### Code Example: A labeled form control with a hint for passwords

```html
<!-- Good: Semantic forms with hints for passwords -->
<form>
  <label for="pwd">Password:</label>
  <span id="pwd-hint">Must contain at least 8 characters.</span>
  <input id="pwd" type="password" aria-describedby="pwd-hint" autocomplete="current-password" required>
</form>
```

### Input assistance and validation

- **Mandatory - Use the `autocomplete` attribute:** Apply the `autocomplete` attribute to `<input>`, `<textarea>`, and `<select>` elements that explicitly collect personal information about the user, and set it to the correct value (for example `"email"` or `"given-name"`). (1.3.5 Identify Input Purpose (Level AA))
- **Provide form validation constraints:** Use `required` (or `aria-required="true"` only when `required` isn't applicable) to signal mandatory inputs. (4.1.2 Name, Role, Value (Level A))
- **Don't trigger context shifts on focus changes:** Avoid auto-submitting forms or jumping pages on focus change events alone. (3.2.1 On Focus (Level A), 3.2.2 On Input (Level A))

## 8. Live Regions

Live regions let assistive tech announce content updates that aren't tied to navigation or focus changes. They're easy to misuse — too many regions, or noisy ones, quickly become spam for screen-reader users.

### Live Region Urgency Table

| Urgency | Visual Analogue | `aria-live` Value | Behavioral Impact | Example |
| :--- | :--- | :--- | :--- | :--- |
| **Critical** | Modal / Alert | `assertive` (or `role="alert"`) | Interrupts immediately, clears speech queue | Session timeout, API failure |
| **Standard**| Toast / Banner | `polite` | Announces at next graceful break | Search results, "Saved" status |
| **Passive**  | Silent text | `off` | Only if user navigates to it | Live character count |

**Heuristic Rule:** Use `assertive` only for critical, time-sensitive updates that require immediate attention or prevent safe continuation (e.g., data loss, session timeouts, or network drops).

### When to announce live regions

- **Announce dynamic errors via live regions:** Use `aria-live` or shift focus to error lists (4.1.3 Status Messages (Level AA)).
- **Don't use live regions for interstitial states** like "Loading…" or "Updating…" unless they're meaningfully informative — they usually just create noise. Use the HTML `<progress>` element or the ARIA `progressbar` role for this purpose instead. (Best Practice)

```html
<!-- Session Timeout Warning with controls -->
<div role="alert" class="timeout-warning">
  Your session will expire in 2 minutes.
  <button type="button" onclick="extendSession()">Extend Session</button>
</div>
```

### Managing announcements

- **Centralize live regions for non-visible announcements:** A single `polite` region and a single `assertive` region per page (with whatever `aria-atomic` configuration you need) keeps announcements consistent and easier to maintain. Many frameworks ship their own announcer abstraction — use it. (Best Practice)
- **Debounce frequently-changing regions:** If a region can update many times per second (e.g. a combobox's result count as the user types), debounce so users aren't spammed. (Best Practice)
- **Delay slightly when other announcements may collide:** When the user is typing or focus is being managed, a small delay before announcing keeps live-region updates from overlapping other speech. (Best Practice)
- **Don't add live-region updates to inert DOM:** When dialogs open or sections become `inert`, queued or debounced messages will be unannounced — or announced from DOM the user can't reach. Coordinate live-region updates with dialog/inert state changes. (4.1.3 Status Messages (Level AA))

## 9. Color

See `color` (via `npx -y modern-web-guidance@latest retrieve "color"`) for accessible color (contrast requirements, light and dark color schemes, Forced Colors Mode, etc).

## 10. Typography

See `typography` (via `npx -y modern-web-guidance@latest retrieve "typography"`) for readable typography.

## 11. Motion and Preferences

See `motion` (via `npx -y modern-web-guidance@latest retrieve "motion"`).

## 12. Modals and Native Dialogs

Modern browsers provide native solutions for creating modal dialogs which avoid the need for focus traps, managing the accessibility of outside content, ensuring the content is on top, and dimming the background content — all of which are error prone and require heavy JavaScript event tracking to maintain.

### Native `<dialog>`

- **Use the native `<dialog>` element:** Invoke the dialog using the `.showModal()` method to open it in a modal state. When in a modal state, the browser sets outside content as inert (i.e. the outside content is hidden from the accessibility tree and cannot be interacted with nor be focused). (1.3.2 Meaningful Sequence (Level A), 2.4.3 Focus Order (Level A), 4.1.2 Name, Role, Value (Level A))
  - **Note:** it is still possible to navigate to the browser chrome when using the `<dialog>` element.
- **Don't implement focus traps for native modal dialogs:** When a `<dialog>` element is opened in a modal state, browsers set outside content as inert which is sufficient for ensuring only the dialog’s content can be focused. (Best Practice)

#### Code Example: HTML & JavaScript: Native `<dialog>` with standard close events

```html
<!-- Dialog opens natively with showModal() and locks focus -->
<button id="open-btn">Open Dialog</button>

<dialog id="accessible-modal" aria-labelledby="title-id">
  <h2 id="title-id">Account Settings</h2>
  <p>Update your details here.</p>
  <button onclick="this.closest('dialog').close()">Close Dialog</button>
</dialog>

<script>
  document.getElementById('open-btn').addEventListener('click', () => {
    document.getElementById('accessible-modal').showModal();
  });
</script>
```

### Custom overlays

- **Use the `inert` attribute for custom overlays:** When `<dialog>` cannot be used (e.g., some non-modal overlays, framework constraints, or layouts where `<dialog>`'s top-layer/positioning behavior conflicts with the design), apply `inert` to outside content to ensure it cannot be interacted with by keyboard, pointer, or assistive technology. This requires structuring elements in such a way that the custom overlay is not a descendant of the element with `inert` set on it. (1.3.2 Meaningful Sequence (Level A), 2.4.3 Focus Order (Level A))
- **Apply `role="dialog"` to the custom overlay:** When applied to the element used as the container for the custom overlay, it ensures that it is exposed as a dialog box to assistive technologies. (4.1.2 Name, Role, Value (Level A))
- **Move focus to the overlay:** Ensure keyboard and screen reader focus moves to the container for the overlay so that people using a screen reader and people using the keyboard alone can start navigating its contents. Don't leave focus in outside content. (1.3.2 Meaningful Sequence (Level A), 2.4.3 Focus Order (Level A))

## 13. Testing Validations

### Automated checks

- **Run Automated checks via axe-core or Lighthouse audits:** Catch missing alt texts or low contrasts (e.g., via Lighthouse in Chrome DevTools MCP).
- **Don't rely purely on scores:** A 100% score does not guarantee real usability.

### Manual testing

- **Validate Sequential Navigations using keyboards alone:** Using only keyboard shortcuts, such as <kbd>Tab</kbd> / <kbd>Shift</kbd> + <kbd>Tab</kbd>, arrow keys, <kbd>Enter</kbd>, <kbd>Space</kbd>, and <kbd>Esc</kbd>, confirm every interactive element is reachable and operable, and that focus never gets stuck.
- **Test on Screen Readers with calibrated browsers:** Rely on standard bindings (e.g., JAWS with Chrome, NVDA with Firefox, Narrator with Edge, VoiceOver with Safari on macOS and iOS, TalkBack with Chrome for Android).

