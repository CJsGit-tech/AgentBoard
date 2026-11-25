import type { CSSProperties, ReactNode } from "react";
import { type Page, type Row, type Change, type Kind, type Workspace, single, stamp, tone } from "./model";

type IconName = Page | "arrow" | "plus" | "trash" | "list" | "board" | "browse" | "search" | "filters" | "columns" | "build" | "bug" | "folder" | "file" | "link" | "edit" | "warning" | "calendar" | "Product" | "Architecture" | "Design" | "Review" | "Unclassified";
export function Icon({ page }: { page: IconName }) {
  return (
    <svg className="icon" viewBox="0 0 256 256" aria-hidden="true" focusable="false">
      <use href={"/icons.svg#ab-icon-" + page} />
    </svg>
  );
}
export function Tag({ value }: { value: string }) {
  return (
    <span className="tag" data-state={value} style={{ "--tone": tone(value) } as CSSProperties}>
      <i className="dot" aria-hidden="true" />
      {value}
    </span>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}
export function Item({
  row,
  onClick,
  left,
  right,
}: {
  row: Row;
  onClick: () => void;
  left?: ReactNode;
  right?: ReactNode;
}) {
  return (
    <button className="item" onClick={onClick}>
      {left}
      <span className="name">{row.name}</span>
      {right}
    </button>
  );
}
const relationshipKinds: Record<string, Kind> = {
  project: "projects", milestone: "milestones", role: "roles", ticket: "tickets",
  documents: "documents", output_documents: "documents", source_documents: "documents",
};
function format(v: unknown, field: string, db?: Workspace): string {
  const kind = relationshipKinds[field];
  if (db && kind && v != null && v !== "") {
    const values = Array.isArray(v) ? v : [v];
    return values.length ? values.map(id =>
      db[kind].find(row => row.id === id)?.name ||
      db.trash.find(item => item.k === kind && item.r.id === id)?.r.name ||
      `Unavailable ${single[kind]}`,
    ).join(", ") : "(empty)";
  }
  return v == null || v === ""
    ? "(empty)"
    : Array.isArray(v)
      ? v.join(", ")
      : typeof v === "object"
        ? JSON.stringify(v)
        : String(v);
}
export function History({ entry: l, db }: { entry: Change; db?: Workspace }) {
  return (
    <div className="log">
      <strong>{l.actor}</strong>{l.editor_role && <> ({l.editor_role})</>} · {l.action} <small>{stamp(l.time)}</small>
      <details><summary>{l.changes.length} changed {l.changes.length===1 ? "field" : "fields"}: {l.changes.map(([field])=>field).join(", ")}</summary>
      {l.changes.map(([f, a, b]) => (
        <p key={f}>
          <small>{f} </small>
          {format(a, f, db)} → {format(b, f, db)}
        </p>
      ))}</details>
    </div>
  );
}
