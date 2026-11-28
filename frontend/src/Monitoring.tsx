import { ticketRole } from "./features/tickets/TicketSummary";
import "./features/monitoring/monitoring.css";
import { Avatar } from "@mantine/core";
import { useState } from "react";
import { RunSwimlane } from "./features/charts/RunSwimlane";
import { Empty, Icon, Tag } from "./Common";
import { reviewDecision } from "./features/monitoring/report-view";
import { attentionStates, newestRuns, nameOf, runSubject, single, stamp, type Change, type Editor, type Row, type Workspace } from "./model";

export type RunGrouping = "Day" | "Agent" | "Status" | "None";

const dayLabel = (time?: string) => time ? new Date(time).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }) : "No report time";

export function RunList({ db, rows, grouping, edit }: { db: Workspace; rows: Row[]; grouping: RunGrouping; edit: (editor: Editor) => void }) {
  const [selected, setSelected] = useState("");
  const runs = newestRuns(rows);
  const hasAssistantRuns = runs.some((run) => run.assistant_run_id);
  const prompt = runs.find((run) => run.status === "Waiting for input") || runs.find((run) => attentionStates.includes(run.status || ""));
  if (!runs.length) return <Empty>No matching runs.</Empty>;
  const groups = new Map<string, Row[]>();
  for (const run of runs) {
    const key = grouping === "Day" ? dayLabel(run.updated) : grouping === "Agent" ? run.agent || "Unassigned" : grouping === "Status" ? run.status || "Unspecified" : "";
    groups.set(key, [...(groups.get(key) || []), run]);
  }
  const open = (row: Row) => { setSelected(row.id); edit({ kind: "runs", row }); };
  const pick = (row: Row) => {
    setSelected(row.id);
    requestAnimationFrame(() => {
      const target = document.querySelector<HTMLElement>(`[data-run="${CSS.escape(row.id)}"]`);
      target?.scrollIntoView({ block: "center" });
      target?.querySelector<HTMLElement>(".run-name")?.focus({ preventScroll: true });
    });
  };
  const columns = 5 + (grouping === "Agent" ? 0 : 1) + (hasAssistantRuns ? 1 : 0);
  return <>
    {prompt && <button className="run-prompt" onClick={() => open(prompt)}>
      <span><Tag value={prompt.status || "Unspecified"} /> <small>{prompt.agent}</small></span>
      <strong>{prompt.name} <Icon page="arrow" /></strong>
      <small>{runSubject(db,prompt)} · Last report {stamp(prompt.updated)}</small>
    </button>}
    <section className="cv-card run-swim-card" aria-label="When agents ran">
      <header className="cv-card__head"><div><h2 className="cv-card__title">When agents ran</h2>
        <p className="cv-card__insight">{swimInsight(runs)}</p></div></header>
      <RunSwimlane runs={runs} selected={selected} onPick={pick} />
    </section>
    <div className="tablebox">
      <table className="record-table run-table">
        <thead><tr><th scope="col">Run</th>{grouping !== "Agent" && <th scope="col">Agent</th>}<th scope="col">Role</th><th scope="col">Run status</th><th scope="col">Ticket status</th><th scope="col">Last report</th>{hasAssistantRuns && <th scope="col">Assistant</th>}</tr></thead>
        {[...groups].map(([group, records]) => <tbody key={group}>
          {group && <tr><th scope="rowgroup" colSpan={columns} className="row-group">
            <span className="row-group-label">{grouping === "Agent" && <Avatar size={23} color={group === "Claude" ? "orange" : "forest"}>{group.slice(0, 2).toUpperCase()}</Avatar>}{group} <small>{records.length}</small></span>
          </th></tr>}
          {records.map((row) => { const ticket=db.tickets.find(t=>t.id===row.ticket && t.project===row.project); return <tr className="row" key={row.id} data-run={row.id} data-selected={selected===row.id||undefined} onClick={() => open(row)}>
            <td data-label="Run"><div className="run-cell">
              <button className="plain run-name" onClick={(event) => {event.stopPropagation(); open(row);}}>{row.name}</button>
              {ticket ? <button type="button" className="run-ticket-chip" onClick={(event)=>{event.stopPropagation(); edit({kind:"tickets",row:ticket});}}>
                <Icon page={ticket.work_type === "BUG" ? "bug" : "tickets"} /><span>{ticket.name}</span></button>
                : <span className="run-ticket-chip is-empty">{row.ticket ? "Linked ticket unavailable" : "No linked ticket"}</span>}
            </div></td>
            {grouping !== "Agent" && <td data-label="Agent"><span className="run-agent"><Avatar size={22} color={row.agent === "Claude" ? "orange" : row.agent === "Codex" ? "forest" : "signal"}>{(row.agent || "?").slice(0, 2).toUpperCase()}</Avatar>{row.agent || "Not recorded"}</span></td>}
            <td data-label="Role">{ticket ? ticketRole(db,ticket) : "Not applicable"}</td>
            <td data-label="Run status"><Tag value={row.status || "Unspecified"} /></td>
            <td data-label="Ticket status">{ticket ? <Tag value={ticket.status || "Unspecified"}/> : <small>Not applicable</small>}</td>
            <td data-label="Last report">{stamp(row.updated)}</td>
            {hasAssistantRuns && <td data-label="Assistant">{row.assistant_run_id && <a
              className="link"
              href={`#project/${encodeURIComponent(row.project || "")}/assistant?run=${encodeURIComponent(row.assistant_run_id)}`}
              onClick={(event) => event.stopPropagation()}
            >Run details <Icon page="arrow" /></a>}</td>}
          </tr>; })}
        </tbody>)}
      </table>
    </div>
  </>;
}

function swimInsight(runs: Row[]) {
  const by = new Map<string, number>();
  runs.forEach(run => by.set(run.agent || "Not recorded", (by.get(run.agent || "Not recorded") || 0) + 1));
  const [top, n] = [...by].sort((a, b) => b[1] - a[1])[0] || ["", 0];
  const failed = runs.filter(run => run.status === "Failed").length;
  return `${top} reported ${n} of ${runs.length} runs.${failed ? ` ${failed} failed.` : " None failed."}`;
}

export function ActivityTimeline({ changes, inspect }: { changes: Change[]; inspect: (entry: Change) => void }) {
  if (!changes.length) return <Empty>No matching changes.</Empty>;
  const days = new Map<string, Change[]>();
  for (const entry of [...changes].sort((a, b) => b.time.localeCompare(a.time))) {
    const day = new Date(entry.time).toLocaleDateString(undefined, {year: "numeric", month: "long", day: "numeric"});
    days.set(day, [...(days.get(day) || []), entry]);
  }
  return <div className="event-timeline">{[...days].map(([day, entries]) => <section key={day} className="activity-day">
    <h2>{day}</h2>
    <ol>{entries.map((entry) => {
      const change = entry.changes.find(([field]) => field === "status");
      const decision = reviewDecision(entry);
      const time = new Date(entry.time).toLocaleTimeString(undefined, {hour: "numeric", minute: "2-digit"});
      return <li key={entry.id}><button className="event-entry" onClick={() => inspect(entry)}>
        <time dateTime={entry.time}>{time}</time><span className="event-node"><Icon page={entry.kind} /></span>
        <span className="event-copy"><strong>{entry.name || entry.action + " " + single[entry.kind]}</strong><small>{entry.actor} · {entry.action.toLowerCase()} {single[entry.kind]}</small></span>
        <span className="event-diff">{decision ? <Tag value={decision.result} /> : change ? <>{String(change[1] || "—")} <span aria-hidden="true">→</span><span className="sr-only"> to </span><Tag value={String(change[2] || "—")} /></> : entry.changes.length + (entry.changes.length === 1 ? " field" : " fields")}</span>
        <Icon page="arrow" />
      </button></li>;
    })}</ol>
  </section>)}</div>;
}
