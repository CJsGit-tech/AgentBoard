import { useState, type ReactNode } from "react";
import { Button, RingProgress } from "@mantine/core";
import { deliveryHistory, deliveryChartX, stepPath, agentWorkload } from "./features/dashboard/metrics";
import "./features/dashboard/dashboard.css";
import { Scorecard } from "./features/dashboard/Scorecard";
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
  const tickets = scoped(db.tickets, scope, "tickets"), milestones = scoped(db.milestones, scope, "milestones"), runs = scoped(db.runs, scope, "runs");
  if (!tickets.length && !milestones.length && !runs.length) return <AwaitingData db={db} scope={scope} guide={guide}/>;
  return <Scorecard db={db} scope={scope} go={go} milestone={milestone} />;
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
