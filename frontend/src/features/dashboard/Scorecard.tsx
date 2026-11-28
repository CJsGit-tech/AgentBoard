// Design Profile V5 Dashboard: scorecard against project targets, then trend, mix and milestone scorecard.
import { useEffect, useMemo, useState } from "react";
import { Button, Menu, NativeSelect } from "@mantine/core";
import { Icon, Tag } from "../../Common";
import { attentionReasons, done, isOverdue, nameOf, request, scoped, type Page, type Row, type TicketView, type Workspace } from "../../model";
import { BurnUp, ChartCard, DailyLines, DataTable, Gauge, MeterList, Pie, SparkLine, VsTarget, seriesColors } from "../charts/BI";
import { foldParts, percentOf } from "../charts/chart-math";
import "./scorecard.css";

type Ratio = { value: number; total: number; percent: number | null };
export type ProjectMetrics = {
  range: { start: string; end: string };
  targets: { target_completion: number; target_evidence: number; target_run_success: number; target_median_hours: number };
  tickets: { total: number; statuses: Record<string, number> };
  completion: Ratio; evidence_coverage: Ratio; run_success: Ratio;
  median_hours_to_last_update: number | null;
  done_per_day: { day: string; count: number }[];
  runs_by_agent: Record<string, { total: number; statuses: Record<string, number> }>;
};
const RANGES = [7, 14, 30] as const;
const localDay = (time: number) => { const d = new Date(time); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
const hours = (h: number) => (h < 1 ? `${Math.round(h * 60)} min` : `${h.toFixed(h < 10 ? 1 : 0)} h`);
const median = (xs: number[]) => { if (!xs.length) return null; const s = [...xs].sort((a, b) => a - b); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

/** When each currently Done ticket last became Done, from the project's saved status activity. */
function doneTimes(db: Workspace, tickets: Row[]) {
  const ids = new Set(tickets.filter(t => t.status === "Done").map(t => t.id));
  const at = new Map<string, number>();
  for (const event of db.activity) {
    if (event.kind !== "tickets" || !ids.has(event.record)) continue;
    const status = event.changes.find(change => change[0] === "status");
    const time = Date.parse(event.time);
    if (status && status[2] === "Done" && Number.isFinite(time) && time > (at.get(event.record) ?? 0)) at.set(event.record, time);
  }
  // Fall back to the last edit for done tickets whose transition predates saved history.
  tickets.forEach(t => { if (t.status === "Done" && !at.has(t.id) && t.updated_at) at.set(t.id, Date.parse(t.updated_at)); });
  return at;
}

export function Scorecard({ db, scope, go, milestone }: { db: Workspace; scope: string; go: (page: Page, view?: TicketView) => void; milestone: (id: string) => void }) {
  const [rangeDays, setRangeDays] = useState<(typeof RANGES)[number]>(7);
  const [milestoneId, setMilestoneId] = useState("");
  const [metrics, setMetrics] = useState<ProjectMetrics | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const allTickets = scoped(db.tickets, scope, "tickets"), milestones = scoped(db.milestones, scope, "milestones"), runs = scoped(db.runs, scope, "runs");
  const tickets = milestoneId ? allTickets.filter(t => t.milestone === milestoneId) : allTickets;
  const end = new Date(); end.setHours(0, 0, 0, 0);
  const start = new Date(end); start.setDate(start.getDate() - (rangeDays - 1));
  const startDay = localDay(start.getTime()), endDay = localDay(end.getTime());
  const days = Array.from({ length: rangeDays }, (_, i) => { const d = new Date(start); d.setDate(d.getDate() + i); return localDay(d.getTime()); });

  useEffect(() => {
    let live = true;
    setError("");
    request<ProjectMetrics>(`projects/${encodeURIComponent(scope)}/metrics?start=${startDay}&end=${endDay}&tz_offset=${-new Date().getTimezoneOffset()}`)
      .then(data => { if (live) setMetrics(data); }).catch(err => { if (live) setError(String(err?.message || err)); });
    return () => { live = false; };
  }, [scope, startDay, endDay, db, attempt]);

  const doneAt = useMemo(() => doneTimes(db, allTickets), [db, allTickets]);
  const reasons = attentionReasons(allTickets, runs);
  const flagged = allTickets.filter(t => reasons.has(t.id)), overdue = allTickets.filter(isOverdue);
  const attention = [...new Map([...flagged, ...overdue].map(t => [t.id, t])).values()];

  // Evidence coverage at the end of each day, for done tickets in the current filter.
  const evidence = days.map(day => {
    const dayEnd = new Date(day + "T23:59:59").getTime();
    const doneBy = tickets.filter(t => t.status === "Done" && (doneAt.get(t.id) ?? Infinity) <= dayEnd);
    return doneBy.length ? percentOf(doneBy.filter(t => t.output_documents?.length).length, doneBy.length) : null;
  });
  const t0 = start.getTime(), t1 = end.getTime() + 86400000;
  const burnTickets = tickets.map(t => ({ created: Date.parse(t.created_at || "") || t0, done: t.status === "Done" ? doneAt.get(t.id) ?? null : null }));
  const pins = milestones.filter(m => !milestoneId || m.id === milestoneId).map(m => {
    const work = allTickets.filter(t => t.milestone === m.id);
    const last = Math.max(...work.map(t => doneAt.get(t.id) ?? 0));
    return { at: last, name: m.name, done: work.length > 0 && done(work) === work.length };
  }).filter(p => p.at >= t0 && p.at <= t1);

  const milestoneParts = foldParts(milestones.map(m => ({ name: m.name, value: allTickets.filter(t => t.milestone === m.id).length })), "Other milestones");
  const roleRows = scoped(db.roles, scope, "roles").map(r => ({ name: r.name, value: tickets.filter(t => t.role === r.id).length })).filter(r => r.value).sort((a, b) => b.value - a.value);
  const roleParts = [...roleRows.slice(0, 2), ...(roleRows.length > 2 ? [{ name: "Other roles", value: roleRows.slice(2).reduce((s, r) => s + r.value, 0), folded: roleRows.slice(2).map(r => `${r.name} ${r.value}`) }] : [])];
  const scoreRows = milestones.map(m => {
    const work = allTickets.filter(t => t.milestone === m.id), doneWork = work.filter(t => t.status === "Done");
    const leads = doneWork.map(t => (Date.parse(t.updated_at || "") - Date.parse(t.created_at || "")) / 3600000).filter(Number.isFinite);
    return { m, total: work.length, done: doneWork.length, evidence: doneWork.filter(t => t.output_documents?.length).length, median: median(leads),
      last: Math.max(0, ...work.map(t => Date.parse(t.updated_at || "") || 0)) };
  }).filter(r => r.total);

  const targets = metrics?.targets;
  // Whole percents everywhere, so the headline, gauge and gap always agree.
  const pct = (r?: Ratio) => (r?.percent == null ? null : Math.round(r.percent));
  const missed = metrics && targets ? [
    pct(metrics.completion) !== null && pct(metrics.completion)! < targets.target_completion ? `completion is ${pct(metrics.completion)}%` : "",
    pct(metrics.evidence_coverage) !== null && pct(metrics.evidence_coverage)! < targets.target_evidence ? `evidence is at ${Math.round(pct(metrics.evidence_coverage)!)}%` : "",
    pct(metrics.run_success) !== null && pct(metrics.run_success)! < targets.target_run_success ? `run success is ${Math.round(pct(metrics.run_success)!)}%` : "",
    metrics.median_hours_to_last_update !== null && metrics.median_hours_to_last_update > targets.target_median_hours ? `median time is ${hours(metrics.median_hours_to_last_update)}` : "",
  ].filter(Boolean) : [];
  const evidenceGaps = scoreRows.filter(r => r.done > r.evidence).sort((a, b) => (b.done - b.evidence) - (a.done - a.evidence));
  const agents = Object.entries(metrics?.runs_by_agent || {});
  const leadByDay = days.map(day => median(tickets.filter(t => t.status === "Done" && localDay(doneAt.get(t.id) ?? 0) === day)
    .map(t => (Date.parse(t.updated_at || "") - Date.parse(t.created_at || "")) / 3600000).filter(Number.isFinite)));
  const fmtDay = (day: string) => new Date(day + "T12:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });

  return <div className="v5-dash">
    <header className="heading">
      <div>
        <h1>{nameOf(db, "projects", scope)}</h1>
        <p>{metrics ? <><b>{metrics.completion.value}</b> of {metrics.completion.total} tickets done. {missed.length
          ? <>{missed.length === 1 ? "One target is missed" : `${missed.length} targets are missed`}: {missed.join(", ")}{evidenceGaps[0] && missed.some(x => x.startsWith("evidence")) ? <>; most gaps are in <b>{evidenceGaps[0].m.name}</b></> : null}.</>
          : "Every target is met."}</> : error ? "Metrics are unavailable right now." : "Loading metrics…"}</p>
      </div>
      <Button variant="default" size="sm" className="mast-action" onClick={() => go("tickets")}>Open tickets</Button>
    </header>

    <div className="v5-filters" role="group" aria-label="Dashboard filters">
      <Menu position="bottom-start">
        <Menu.Target><Button variant="default" size="xs" leftSection={<Icon page="calendar" />}>Last {rangeDays} days · {fmtDay(startDay)} – {fmtDay(endDay)} ⌄</Button></Menu.Target>
        <Menu.Dropdown>{RANGES.map(n => <Menu.Item key={n} onClick={() => setRangeDays(n)}>{n === rangeDays ? "✓ " : ""}Last {n} days</Menu.Item>)}</Menu.Dropdown>
      </Menu>
      <NativeSelect size="xs" aria-label="Milestone" value={milestoneId} onChange={e => setMilestoneId(e.currentTarget.value)}
        data={[{ value: "", label: "Milestone: All" }, ...milestones.map(m => ({ value: m.id, label: m.name }))]} />
      <span className="v5-filters__note">Scorecard covers the whole project{milestoneId ? "; charts show the selected milestone" : ""}.</span>
    </div>

    {error && <p className="v5-dash__error" role="alert">{error} <button className="link" onClick={() => setAttempt(n => n + 1)}>Retry</button></p>}

    <section className="v5-kpis" aria-label="Scorecard">
      <article className="v5-kpi">
        <div className="v5-kpi__label">Completion</div>
        <Gauge value={metrics?.completion.value ?? 0} total={metrics?.completion.total ?? 0} target={targets ? targets.target_completion / 100 : undefined} label="Tickets done" />
        <div className="v5-kpi__foot"><span><b>{metrics?.completion.value ?? "–"}</b> of {metrics?.completion.total ?? "–"} tickets done</span>{targets && <VsTarget actual={pct(metrics?.completion)} target={targets.target_completion} />}</div>
      </article>
      <article className="v5-kpi">
        <div className="v5-kpi__label">Evidence coverage</div>
        <Gauge value={metrics?.evidence_coverage.value ?? 0} total={metrics?.evidence_coverage.total ?? 0} target={targets ? targets.target_evidence / 100 : undefined} label="Done tickets with evidence" />
        <div className="v5-kpi__foot"><span><b>{metrics?.evidence_coverage.value ?? "–"}</b> of {metrics?.evidence_coverage.total ?? "–"}{metrics && metrics.evidence_coverage.total > metrics.evidence_coverage.value ? <> · {metrics.evidence_coverage.total - metrics.evidence_coverage.value} missing</> : null}</span>
          {targets && <VsTarget actual={pct(metrics?.evidence_coverage) === null ? null : Math.round(pct(metrics?.evidence_coverage)!)} target={targets.target_evidence} />}</div>
      </article>
      <article className="v5-kpi">
        <div className="v5-kpi__label">Run success</div>
        <Gauge value={metrics?.run_success.value ?? 0} total={metrics?.run_success.total ?? 0} target={targets ? targets.target_run_success / 100 : undefined} label="Finished runs completed" />
        <div className="v5-kpi__foot"><span><b>{metrics?.run_success.value ?? "–"}</b> of {metrics?.run_success.total ?? "–"} finished runs completed</span>
          <span className="v5-kpi__agents" aria-label="Runs by agent in range">{agents.length ? agents.map(([agent, v]) => `${agent} ${v.total}`).join(" · ") : `No runs in the last ${rangeDays} days`}</span>
          {targets && <VsTarget actual={pct(metrics?.run_success) === null ? null : Math.round(pct(metrics?.run_success)!)} target={targets.target_run_success} />}</div>
      </article>
      <article className="v5-kpi">
        <div className="v5-kpi__label">Median time to last update</div>
        <div className="v5-kpi__figure">{metrics?.median_hours_to_last_update != null ? hours(metrics.median_hours_to_last_update) : "–"}
          <SparkLine values={leadByDay} target={targets?.target_median_hours} label={`Median hours by completion day: ${leadByDay.map((v, i) => v === null ? null : `${fmtDay(days[i])} ${hours(v)}`).filter(Boolean).join(", ") || "none"}`} /></div>
        <div className="v5-kpi__foot"><span>From filing to last update of done tickets</span>{targets && <VsTarget actual={metrics?.median_hours_to_last_update ?? null} target={targets.target_median_hours} lowerIsBetter unit=" h" />}</div>
      </article>
    </section>

    {attention.length > 0 && <section className="v5-attention" aria-labelledby="v5-attention-title">
      <div className="v5-section-head"><h2 id="v5-attention-title">Needs attention</h2><button className="link" onClick={() => go("tickets", "attention")}>View all {attention.length} →</button></div>
      <ul>{attention.slice(0, 5).map(t => <li key={t.id}><Tag value={reasons.get(t.id) || (isOverdue(t) ? "Overdue" : t.status || "Unspecified")} />
        <a href={`#tickets/${t.id}`}>{t.name}</a><small>{nameOf(db, "milestones", t.milestone)}</small></li>)}</ul>
    </section>}

    <div className="v5-row">
      <ChartCard title="Scope and delivery" insight={(() => { const open = tickets.length - done(tickets); return open ? `${open} of ${tickets.length} tickets are still open.` : `All ${tickets.length} tickets are done; every rise in scope was matched.`; })()}
        table={<DataTable head={["Day", "Done that day"]} rows={(metrics?.done_per_day || []).map(d => [fmtDay(d.day), d.count])} />}>
        <BurnUp tickets={burnTickets} start={t0} end={t1} pins={pins} label="Scope and delivery" />
      </ChartCard>
      <ChartCard title="Work by milestone" insight={milestoneParts[0] ? `${milestoneParts[0].name} holds ${percentOf(milestoneParts[0].value, allTickets.length)}% of tickets.` : "No tickets yet."}
        table={<DataTable head={["Milestone", "Tickets"]} rows={milestones.map(m => [m.name, allTickets.filter(t => t.milestone === m.id).length])} />}>
        <Pie parts={milestoneParts.map((p, i) => ({ name: p.name, value: p.value, color: p.folded.length ? "var(--c-other)" : seriesColors[i], sub: p.folded.join(" · ") || undefined }))} label="Tickets by milestone" />
      </ChartCard>
    </div>

    <div className="v5-row">
      <ChartCard title="Evidence coverage" insight={targets ? `Coverage of done tickets at each day's end, against the ${targets.target_evidence}% target.${evidenceGaps[0] ? ` ${evidenceGaps[0].m.name} has ${evidenceGaps[0].done - evidenceGaps[0].evidence} done tickets without proof.` : ""}` : undefined}
        table={<DataTable head={["Day", "Coverage"]} rows={days.map((d, i) => [fmtDay(d), evidence[i] === null ? "No done tickets yet" : evidence[i] + "%"])} />}>
        <DailyLines days={days} series={[{ name: "Coverage", color: seriesColors[0], values: evidence }]} max={100} format={v => v + "%"}
          reference={targets ? { value: targets.target_evidence, label: `Target ${targets.target_evidence}%` } : undefined} label="Evidence coverage by day" />
      </ChartCard>
      <ChartCard title="Who carries the work" insight={roleRows[0] ? `${roleRows[0].name} carries ${percentOf(roleRows[0].value, tickets.length)}% of tickets.` : "No roles linked yet."}
        table={<DataTable head={["Role", "Tickets"]} rows={roleRows.map(r => [r.name, r.value])} />}>
        <Pie parts={roleParts.map((p, i) => ({ name: p.name, value: p.value, color: i < 2 ? seriesColors[i] : "var(--c-other)", sub: "folded" in p ? p.folded.join(" · ") : undefined }))} label="Tickets by role" />
      </ChartCard>
    </div>

    <ChartCard title="Milestone scorecard" insight={`${scoreRows.filter(r => r.done === r.total).length} of ${scoreRows.length} milestones are complete.${evidenceGaps.length && targets ? ` ${evidenceGaps.filter(r => percentOf(r.evidence, r.done)! < targets.target_evidence).map(r => r.m.name).join(", ") || "None"} below the evidence target.` : ""}`}>
      <div className="cv-table-wrap v5-score-wrap"><table className="cv-table v5-score">
        <thead><tr><th scope="col">Milestone</th><th scope="col">Tickets</th><th scope="col">Completion</th><th scope="col">Evidence{targets ? ` · target ${targets.target_evidence}%` : ""}</th><th scope="col">Median time</th><th scope="col">Last update</th></tr></thead>
        <tbody>{scoreRows.map(r => <tr key={r.m.id}>
          <th scope="row"><button className="link" onClick={() => milestone(r.m.id)}>{r.m.name}</button></th>
          <td>{r.total}</td>
          <td><MeterList rows={[{ key: `${r.m.name} completion`, name: "", value: r.done, total: r.total, target: targets ? targets.target_completion / 100 : undefined, figure: `${r.done}/${r.total}` }]} /></td>
          <td>{r.done ? <MeterList rows={[{ key: `${r.m.name} evidence`, name: "", value: r.evidence, total: r.done, target: targets ? targets.target_evidence / 100 : undefined, figure: `${percentOf(r.evidence, r.done)}%` }]} /> : <small>No done tickets</small>}</td>
          <td>{r.median === null ? "–" : hours(r.median)}</td>
          <td>{r.last ? new Date(r.last).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "–"}</td>
        </tr>)}</tbody>
      </table></div>
    </ChartCard>
  </div>;
}
