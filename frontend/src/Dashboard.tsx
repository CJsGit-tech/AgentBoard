import { useState, type ReactNode } from "react";
import { Button, RingProgress } from "@mantine/core";
import { deliveryHistory, deliveryChartX, stepPath, agentWorkload } from "./features/dashboard/metrics";
import "./features/dashboard/dashboard.css";
import { Empty, Icon, Tag } from "./Common";
import { InfoHelp } from "./features/help/InfoHelp";
import {
  type Row,
  type Workspace,
  type Page,
  type TicketView,
  attentionReasons,
  done,
  isOverdue,
  nameOf,
  percent,
  projectRunAlerts,
  scoped,
  shortDate,
} from "./model";

const statusOrder = ["Done", "In progress", "Blocked", "Planned"] as const;
const statusKey: Record<string, string> = {
  Done: "done",
  "In progress": "progress",
  Blocked: "blocked",
  Planned: "planned",
  Unspecified: "unspecified",
};
const deliveryTime = new Intl.DateTimeFormat(undefined, {
  year: "numeric", month: "short", day: "numeric", hour: "numeric", minute: "2-digit", second: "2-digit",
});

function normalizedStatus(ticket: Row) {
  return statusOrder.includes(ticket.status as (typeof statusOrder)[number])
    ? ticket.status!
    : "Unspecified";
}

function counts(tickets: Row[]) {
  const known = statusOrder.map((status) => ({
    status,
    key: statusKey[status],
    count: tickets.filter((ticket) => normalizedStatus(ticket) === status).length,
  }));
  const unspecified = tickets.filter((ticket) => normalizedStatus(ticket) === "Unspecified").length;
  return unspecified ? [...known, { status: "Unspecified", key: statusKey.Unspecified, count: unspecified }] : known;
}

/** One segment per ticket; very large projects use proportional status segments. */
export function Meter({ tickets, label }: { tickets: Row[]; label?: string }) {
  const parts = counts(tickets);
  if (!tickets.length) {
    return <div className="meter is-empty" role="img" aria-label="Progress pending" />;
  }

  const summary = label || `${done(tickets)} of ${tickets.length} tickets complete` +
    parts.filter((part) => part.status !== "Done" && part.count)
      .map((part) => ` · ${part.count} ${part.status.toLowerCase()}`).join("");
  const dense = tickets.length > 36;
  return (
    <div
      className={`meter${dense ? " is-dense" : ""}`}
      role="img"
      aria-label={summary}
      style={dense
        ? { gridTemplateColumns: parts.filter((part) => part.count).map((part) => `${part.count}fr`).join(" ") }
        : undefined}
    >
      {dense
        ? parts.filter((part) => part.count).map((part) => <i key={part.key} data-s={part.key} />)
        : parts.flatMap((part) => Array.from({ length: part.count }, (_, index) =>
          <i key={`${part.key}-${index}`} data-s={part.key} />,
        ))}
    </div>
  );
}

export function CompletionDial({ tickets, compact = false }: { tickets: Row[]; compact?: boolean }) {
  if (!tickets.length) return <Empty>No tickets yet.</Empty>;
  const progress = percent(tickets);
  return (
    <figure className={compact ? "completion-dial compact-dial" : "completion-dial"}>
      <div className="dial-face" role="img" aria-label={`${progress}% of tickets complete`}>
        <RingProgress
          aria-hidden="true"
          size={compact ? 108 : 170}
          thickness={compact ? 6 : 10}
          rootColor="#e3e7ec"
          sections={[{ value: progress, color: "var(--signal)" }]}
          roundCaps
          label={<span className="dial-number">{progress}<small>%</small></span>}
        />
      </div>
      <figcaption>{done(tickets)} of {tickets.length} complete</figcaption>
    </figure>
  );
}

function DecisionCard({ tone, title, count, href, note, children }: {
  tone: "amber" | "red";
  title: string;
  count: number;
  href: string;
  note: string;
  children?: ReactNode;
}) {
  return (
    <section className="decision card" data-tone={count ? tone : "clear"} aria-label={title}>
      <a className="decision-link" href={href}>
        <span className="decision-label">
          <Icon page={tone === "red" ? "calendar" : "warning"} />{title}
        </span>
        <strong>{count}</strong>
        <span className="decision-go">View tickets <Icon page="arrow" /></span>
      </a>
      <p className="decision-note">{note}</p>
      {children}
    </section>
  );
}

function DecisionItem({ href, title, context, status }: {
  href: string;
  title: string;
  context: string;
  status: string;
}) {
  return (
    <li>
      <a href={href}>
        <span><b>{title}</b><small>{context}</small></span>
        <Tag value={status} />
      </a>
    </li>
  );
}

export function Dashboard({ db, scope, go, milestone, guide }: {
  db: Workspace; scope: string; go: (page: Page, view?: TicketView) => void;
  milestone: (id: string) => void; guide?: () => void;
}) {
  const [checkpoint, inspect] = useState<{ scope: string; time: number } | null>(null);
  const tickets = scoped(db.tickets, scope, "tickets"), milestones = scoped(db.milestones, scope, "milestones"), runs = scoped(db.runs, scope, "runs");
  const reasons = attentionReasons(tickets, runs), flagged = tickets.filter(t => reasons.has(t.id)), overdue = tickets.filter(isOverdue);
  const projectAlerts = projectRunAlerts(runs);
  const workload = agentWorkload(runs, [], tickets, db.roles);
  const milestonesWithWork = milestones.map(record => ({ record, work: tickets.filter(ticket => ticket.milestone === record.id) }));
  const next = milestonesWithWork.find(({ work }) => done(work) < work.length);
  const ticketById = new Map(tickets.map(ticket => [ticket.id, ticket]));
  const history = deliveryHistory(tickets, db.activity), last = history.points.at(-1);
  const inspected = (checkpoint?.scope === scope && history.checkpoints.find(p => p.time === checkpoint.time)) || history.checkpoints.at(-1);
  const max = Math.max(1, ...history.points.map(p => p.total));
  const chartCursor = inspected && last ? deliveryChartX(inspected.time, history.points[0].time, last.time) : null;
  if (!tickets.length && !milestones.length && !runs.length) return <AwaitingData db={db} scope={scope} guide={guide}/>;
  return <div className="bi-dashboard">
    <h1 className="sr-only">Project dashboard</h1>
    <div className="bi-hero"><div className="bi-summary">
      <section className="bi-attention"><div className="bi-section-head"><h2>Needs attention</h2></div>
        <div className="bi-health-values"><button onClick={() => go("tickets", "attention")}><strong>{flagged.length}</strong><span>Tickets needing review</span></button><button onClick={() => go("tickets", "overdue")}><strong>{overdue.length}</strong><span>Overdue tickets</span></button></div>
        {projectAlerts.length > 0 && <button className="link" onClick={() => go("runs")}>{projectAlerts.length} project runs need attention</button>}
      </section>
      <section className="bi-next-milestone">
        <div className="bi-section-head"><h2>Next milestone</h2><button className="link" onClick={() => go("milestones")}>View milestones →</button></div>
        {next ? <MilestoneProgress {...next} open={milestone}/> : <Empty>{milestones.length ? "No unfinished milestones with tickets." : "No milestones saved."}</Empty>}
      </section>
    </div><div className="bi-main-row">
      <section className="bi-trend"><div className="bi-section-head"><div className="with-info"><h2>Recorded delivery</h2><InfoHelp label="recorded delivery">Current ticket cohort · saved status history</InfoHelp></div></div>
        {last ? <><p className="bi-note">Solid green: Done · Dashed gray: Tickets recorded</p><svg viewBox="0 0 640 204" className="bi-line-chart" role="img" aria-label={`Recorded delivery: ${last.done} of ${last.total} recorded tickets done`}>
          {[...new Set([0,Math.round(max/2),max])].map(value => <g key={value}><line x1="38" x2="624" y1={174-value/max*156} y2={174-value/max*156} stroke="var(--line)"/><text x="27" y={178-value/max*156} textAnchor="end" className="bi-axis-text">{value}</text></g>)}
          <path d={stepPath(history.points,"total")} fill="none" stroke="var(--muted)" strokeDasharray="4 4"/><path d={stepPath(history.points,"done")} fill="none" stroke="var(--teal)" strokeWidth="2.8"/>
          {inspected && chartCursor !== null && <g aria-hidden="true">
            <line x1={chartCursor} x2={chartCursor} y1={18} y2={174} stroke="var(--muted)" strokeDasharray="3 4"/>
            <circle cx={chartCursor} cy={174 - inspected.done / max * 156} r={4} fill="var(--surface)" stroke="var(--teal)" strokeWidth={2}/>
          </g>}
        </svg><div className="bi-inspect"><label htmlFor="delivery-checkpoint">Inspect recorded step</label><select id="delivery-checkpoint" value={inspected?.time} onChange={e=>inspect({scope,time:Number(e.target.value)})}>{history.checkpoints.map(point => <option key={point.time} value={point.time}>{deliveryTime.format(point.time)} · {point.done} of {point.total} done</option>)}</select></div>
        {inspected && <div className="bi-checkpoint">
          <p role="status" className="bi-chart-readout">{inspected.done} of {inspected.total} recorded tickets done · {inspected.changes.length} saved status {inspected.changes.length === 1 ? "change" : "changes"}</p>
          {inspected.changes.length > 0 && <ul aria-label="Ticket status changes at this step">{inspected.changes.map(change => <li key={change.id}>
            <a href={`#tickets/${change.ticketId}`}>{ticketById.get(change.ticketId)?.name || change.ticketId}</a>
            <span>{change.to === null ? `Removed from recorded totals · previously ${change.from}` : change.from ? `${change.from} → ${change.to}` : change.created ? `Created as ${change.to}` : `Recorded as ${change.to} · previous status unavailable`}</span>
          </li>)}</ul>}
        </div>}
        {!history.complete && <p className="bi-note">History covers {history.covered} of {tickets.length} current tickets.</p>}{!history.matchesCurrent && <p className="bi-note">The latest saved board status differs from the available history.</p>}</> : <Empty>A trend appears when ticket status changes are recorded.</Empty>}
        {history.unavailable > 0 && <p className="bi-note">Some saved status changes could not be read. The trend may be incomplete.</p>}
      </section>
      <section className="bi-delivery-summary"><div className="bi-section-head"><h2>Ticket completion</h2></div>
        <div className="bi-completion"><CompletionDial tickets={tickets} compact/>{tickets.length > 0 && <dl className="bi-ticket-breakdown">{counts(tickets).map(part => <div key={part.key}><dt>{part.status}</dt><dd>{part.count}</dd></div>)}</dl>}</div>
      </section>
    </div></div>
    {milestonesWithWork.some(item => item !== next) && <section className="bi-other-milestones">
      <div className="bi-section-head"><h2>{next ? "Other milestones" : "Milestone progress"}</h2></div>
      <div className="bi-milestone-grid">{milestonesWithWork.filter(item => item !== next).map(item => <MilestoneProgress key={item.record.id} {...item} open={milestone}/>)}</div>
    </section>}
    <section className="agent-workload" aria-label="Reported agent workload">
      <div className="bi-section-head"><div className="with-info"><h2>Agent workload</h2><InfoHelp label="agent workload">Last reported states. Completed reports count as past work.</InfoHelp></div><button className="link" onClick={() => go("runs")}>View reports →</button></div>
      {workload.agents.length > 0 ? <ul className="workload-agents">{workload.agents.map(agent => <li key={agent.agent}>
        <b>{agent.agent}</b><span>{agent.active.length ? `${agent.running} running · ${agent.queued} queued · ${agent.waiting} waiting or blocked` : agent.state === "Unknown" ? "Activity unavailable" : "Idle"}</span>
      </li>)}</ul> : <p className="bi-note">No agent reports yet.</p>}
    </section>
  </div>;
}

function MilestoneProgress({ record, work, open }: { record: Row; work: Row[]; open: (id: string) => void }) {
  return <article>
    <h3><button className="plain" onClick={() => open(record.id)}>{record.name}</button></h3>
    <div className="bi-meter-label"><strong>{work.length ? `${percent(work)}%` : "Progress pending"}</strong>{work.length > 0 && <span>{done(work)} of {work.length} tickets done</span>}</div>
    <Meter tickets={work}/>
  </article>;
}

/** Empty project state: no activity is reported as zero or overdue. */
export function AwaitingData({ db, scope, guide }: {
  db: Workspace;
  scope: string;
  guide?: () => void;
}) {
  return (
    <div className="dash">
      <section className="awaiting" aria-labelledby="awaiting-title">
        <div className="awaiting-copy">
          <p className="eyebrow">Report not started</p>
          <div className="with-info"><h2 id="awaiting-title">Waiting for project work</h2><InfoHelp label="project progress">Progress will appear when tickets and milestones are added. Until then, nothing here is late or behind; there is simply nothing to measure yet.</InfoHelp></div>
          {guide && <div className="awaiting-actions">
            <Button onClick={guide} leftSection={<Icon page="file" />}>Open AgentBuild Guide</Button>
          </div>}
        </div>
        <ol className="awaiting-steps" aria-label="What fills this report">
          {[
            ["Tickets", "Create scoped work from project requirements."],
            ["Milestones", "Group tickets into delivery stages."],
            ["Runs", "Record each agent run against a ticket."],
          ].map(([name, description], index) => (
            <li key={name}>
              <span className="step-no" aria-hidden="true">{index + 1}</span>
              <div><b>{name}</b><small>{description}</small></div>
              <span className="step-value" aria-label={`${name}: no data yet`}>—</span>
            </li>
          ))}
        </ol>
      </section>
      <div className="ghost-row" aria-hidden="true">
        {["Needs attention", "Overdue", "Overall progress"].map((name) => (
          <div key={name} className="ghost"><span>{name}</span><b>—</b><i /></div>
        ))}
      </div>

    </div>
  );
}
