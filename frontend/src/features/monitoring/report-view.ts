import type { Change, Row } from "../../model";

function savedText(changes: Change["changes"], field: string) {
  const value = changes.find(([name]) => name === field)?.[2];
  return typeof value === "string" ? value.trim() : "";
}

export function reviewDecision(entry: Change) {
  const result = savedText(entry.changes, "Review result");
  if (!result) return null;

  return {
    result,
    rationale: savedText(entry.changes, "Rationale") || savedText(entry.changes, "Scope decision"),
    decidedBy: savedText(entry.changes, "Decision by"),
  };
}

export function runReportNotes(run: Row, history: Change[]) {
  const creation = history.find(entry => entry.action === "Created");
  const savedInitial = creation?.changes.find(([name]) => name === "note")?.[2];
  const initial = typeof savedInitial === "string" && savedInitial.trim() ? savedInitial : "";
  const initialStatus = creation ? savedText(creation.changes, "status") : "";
  const recorded = run.note || "";
  // Separate only an exact audit-history prefix so edits to the original report remain visible in full.
  const appended = initial && recorded.startsWith(initial) ? recorded.slice(initial.length).trim() : "";
  const latest = recorded.trim();
  const same = Boolean(initial && latest === initial.trim());
  const unchanged = Boolean(same && ["Queued", "Running", "Waiting for input"].includes(initialStatus)
    && ["Completed", "Failed", "Cancelled"].includes(run.status || ""));

  return { latest: appended || latest, initial: same ? "" : initial, unchanged };
}
