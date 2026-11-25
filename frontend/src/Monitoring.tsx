import { TicketSummary, ticketRole, ticketMilestone } from "./features/tickets/TicketSummary";
import "./features/monitoring/monitoring.css";
import { Avatar } from "@mantine/core";
import { Empty, Icon, Tag } from "./Common";
import { attentionStates, newestRuns, nameOf, runSubject, single, stamp, type Change, type Editor, type Row, type Workspace } from "./model";

export type RunGrouping = "Agent" | "Status" | "None";

export function RunList({ db, rows, grouping, edit }: { db: Workspace; rows: Row[]; grouping: RunGrouping; edit: (editor: Editor) => void }) {
  const runs = newestRuns(rows);
  const hasAssistantRuns = runs.some((run) => run.assistant_run_id);
  const prompt = runs.find((run) => run.status === "Waiting for input") || runs.find((run) => attentionStates.includes(run.status || ""));
  if (!runs.length) return <Empty>No matching runs.</Empty>;
  const groups = new Map<string, Row[]>();
  for (const run of runs) {
    const key = grouping === "Agent" ? run.agent || "Unassigned" : grouping === "Status" ? run.status || "Unspecified" : "";
    groups.set(key, [...(groups.get(key) || []), run]);
  }
  const open = (row: Row) => edit({ kind: "runs", row });
  return <>
    {prompt && <button className="run-prompt" onClick={() => open(prompt)}>
      <span><Tag value={prompt.status || "Unspecified"} /> <small>{prompt.agent}</small></span>
      <strong>{prompt.name} <Icon page="arrow" /></strong>
      <small>{runSubject(db,prompt)} · Last report {stamp(prompt.updated)}</small>
    </button>}
    <div className="tablebox">
      <table className="record-table">
        <thead><tr><th scope="col">Run</th>{grouping !== "Agent" && <th scope="col">Agent</th>}<th scope="col">Run status</th><th scope="col">Linked work</th><th scope="col">Ticket role</th><th scope="col">Ticket status</th><th scope="col">Last report</th>{hasAssistantRuns && <th scope="col">Assistant</th>}</tr></thead>
        {[...groups].map(([group, records]) => <tbody key={group}>
          {group && <tr><th scope="rowgroup" colSpan={(grouping === "Agent" ? 6 : 7) + (hasAssistantRuns ? 1 : 0)} className="row-group">
            <span className="row-group-label">{grouping === "Agent" && <Avatar size={23} color={group === "Claude" ? "orange" : "forest"}>{group.slice(0, 2).toUpperCase()}</Avatar>}{group} <small>{records.length}</small></span>
          </th></tr>}
          {records.map((row) => { const ticket=db.tickets.find(t=>t.id===row.ticket && t.project===row.project); return <tr className="row" key={row.id} onClick={() => open(row)}>
            <td data-label="Run"><div className="entry-name"><Icon page="runs" /><div><button className="plain" onClick={(event) => {event.stopPropagation(); open(row);}}>{row.name}</button><small>{runSubject(db, row)}</small></div></div></td>
            {grouping !== "Agent" && <td data-label="Agent">{row.agent || "Not recorded"}</td>}
            <td data-label="Run status"><Tag value={row.status || "Unspecified"} /></td>
            <td data-label="Linked work">{ticket ? <TicketSummary db={db} ticket={ticket} open={t=>edit({kind:"tickets",row:t})}/> : row.ticket ? "Linked ticket unavailable" : "No linked ticket"}</td>
            <td data-label="Ticket role">{ticket ? ticketRole(db,ticket) : "Not applicable"}</td>
            <td data-label="Ticket status">{ticket ? <Tag value={ticket.status || "Unspecified"}/> : "Not applicable"}</td>
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
      const time = new Date(entry.time).toLocaleTimeString(undefined, {hour: "numeric", minute: "2-digit"});
      return <li key={entry.id}><button className="event-entry" onClick={() => inspect(entry)}>
        <time dateTime={entry.time}>{time}</time><span className="event-node"><Icon page={entry.kind} /></span>
        <span className="event-copy"><strong>{entry.name || entry.action + " " + single[entry.kind]}</strong><small>{entry.actor} · {entry.action.toLowerCase()} {single[entry.kind]}</small></span>
        <span className="event-diff">{change ? <>{String(change[1] || "—")} <span aria-hidden="true">→</span><span className="sr-only"> to </span><Tag value={String(change[2] || "—")} /></> : entry.changes.length + (entry.changes.length === 1 ? " field" : " fields")}</span>
        <Icon page="arrow" />
      </button></li>;
    })}</ol>
  </section>)}</div>;
}
