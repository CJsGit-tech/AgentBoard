import { useEffect, useId, useRef, useState } from "react";
import "./help.css";

// Mantine 7 derives describedBy from its wrapper and overwrites the input prop.
// Run after each render, retaining its validation-error relation as well as help.
export function describeWithHelp(id: string) {
  return (input: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | null) => {
    if (input) input.setAttribute("aria-describedby", [...new Set([
      ...(input.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean), id,
    ])].join(" "));
  };
}

/** Supplementary text only. Requirements, errors and current status stay inline. */
export function InfoHelp({ label, children, id }: { label: string; children: string; id?: string }) {
  const generated = useId();
  const helpId = id || `help-${generated}`;
  const trigger = useRef<HTMLButtonElement>(null);
  const hint = useRef<HTMLSpanElement>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const target = hint.current!, button = trigger.current!;
    let frame = 0;
    const isOpen = () => target.matches(":is(:popover-open, .\\:popover-open)");
    const position = () => {
      const anchor = button.getBoundingClientRect();
      const width = Math.min(304, window.innerWidth - 24);
      target.style.width = `${width}px`;
      target.style.left = `${Math.max(12, Math.min(anchor.left, window.innerWidth - width - 12))}px`;
      const height = target.getBoundingClientRect().height;
      const below = anchor.bottom + 6;
      target.style.top = `${Math.max(12, below + height <= window.innerHeight - 12 ? below : anchor.top - height - 6)}px`;
    };
    const beforeToggle = (event: Event) => {
      if ((event as ToggleEvent).newState !== "open") return;
      // Older Safari recognizes popovers but treats hint as manual. Keep light dismissal.
      if (target.popover !== "hint") target.setAttribute("popover", "auto");
      position();
      frame = requestAnimationFrame(position);
    };
    const toggle = () => { setOpen(isOpen()); if (isOpen()) position(); };
    const reposition = () => { if (isOpen()) position(); };
    target.addEventListener("beforetoggle", beforeToggle);
    target.addEventListener("toggle", toggle);
    window.addEventListener("resize", reposition);
    window.addEventListener("scroll", reposition, true);
    return () => {
      cancelAnimationFrame(frame);
      target.removeEventListener("beforetoggle", beforeToggle);
      target.removeEventListener("toggle", toggle);
      window.removeEventListener("resize", reposition);
      window.removeEventListener("scroll", reposition, true);
    };
  }, []);

  return <span className="info-help">
    <button ref={trigger} type="button" className="info-help-trigger" aria-label={`About ${label}`}
      aria-expanded={open} aria-controls={helpId}
      {...{ interestfor: helpId, popovertarget: helpId, popovertargetaction: "show" }}>
      <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7.25"/><path d="M10 9v5M10 6v.5"/></svg>
    </button>
    <span ref={hint} id={helpId} role="tooltip" {...{ popover: "hint" }} className="info-help-content">{children}</span>
  </span>;
}
