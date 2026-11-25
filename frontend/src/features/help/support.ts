// Load compatibility code only where the platform feature is absent.
export async function prepareHelp() {
  if (!("popover" in HTMLElement.prototype)) await import("@oddbird/popover-polyfill");
  if (!("interestForElement" in HTMLButtonElement.prototype)) await import("interestfor");
  // Register before dialogs: Mantine handles Escape at window capture, before document.
  window.addEventListener("keydown", event => {
    if (event.key !== "Escape" || event.isComposing) return;
    const hint = document.querySelector<HTMLElement>(".info-help-content:is(:popover-open, .\\:popover-open)");
    if (!hint) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    hint.hidePopover();
  }, true);
}
