// Ranked horizontal bars of linked tickets per role, split Build / Bug, with a Table view.
import { useState } from "react";
import { SegmentedControl } from "@mantine/core";
import { Legend } from "./primitives";

export type RoleLoad = { role: string; build: number; bug: number; other: number };

export function RoleBars({ rows, title, insight }: { rows: RoleLoad[]; title: string; insight: string }) {
  const [mode, setMode] = useState("Chart");
  const ranked = [...rows].sort((a, b) => total(b) - total(a));
  const max = Math.max(1, ...ranked.map(total));
  return (
    <figure className="cv-card">
      <header className="cv-card__head">
        <div><h2 className="cv-card__title">{title}</h2><p className="cv-card__insight">{insight}</p></div>
        <div className="cv-card__tools">
          <Legend items={[{ label: "Build", color: "var(--c-s1)" }, { label: "Bug", color: "var(--c-s2)" }, ...(ranked.some(r => r.other) ? [{ label: "Unclassified", color: "var(--c-other)" }] : [])]} />
          <SegmentedControl size="xs" radius="xl" value={mode} onChange={setMode} data={["Chart", "Table"]} aria-label={title + " view"} />
        </div>
      </header>
      {mode === "Table" ? (
        <div className="cv-table-wrap"><table className="cv-table">
          <thead><tr><th>Role</th><th>Build</th><th>Bug</th><th>Unclassified</th><th>Total</th></tr></thead>
          <tbody>{ranked.map(r => <tr key={r.role}><td>{r.role}</td><td>{r.build}</td><td>{r.bug}</td><td>{r.other}</td><td>{total(r)}</td></tr>)}</tbody>
        </table></div>
      ) : (
        <ul className="cv-bars" role="list">
          {ranked.map(r => (
            <li key={r.role} aria-label={`${r.role}: ${total(r)} tickets, ${r.build} build, ${r.bug} bug${r.other ? `, ${r.other} unclassified` : ""}`}>
              <span className="cv-bars__name">{r.role}</span>
              <span className="cv-bars__track">
                {total(r) ? <span className="cv-bars__fill" style={{ width: `${(total(r) / max) * 100}%` }}>
                  {r.build > 0 && <i style={{ flexGrow: r.build, background: "var(--c-s1)" }} title={`Build ${r.build}`} />}
                  {r.bug > 0 && <i style={{ flexGrow: r.bug, background: "var(--c-s2)" }} title={`Bug ${r.bug}`} />}
                  {r.other > 0 && <i style={{ flexGrow: r.other, background: "var(--c-other)" }} title={`Unclassified ${r.other}`} />}
                </span> : <span className="cv-bars__zero" />}
              </span>
              <b>{total(r)}</b>
            </li>
          ))}
        </ul>
      )}
    </figure>
  );
}
const total = (r: RoleLoad) => r.build + r.bug + r.other;
