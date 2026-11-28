// Design Profile V5 Portfolio report (decision D): read-only comparison of every project.
import { useEffect, useState } from "react";
import { Button, Menu } from "@mantine/core";
import { Icon } from "../../Common";
import { request, type Workspace } from "../../model";
import { ChartCard, DailyLines, DataTable, Gauge, MeterList, Pie, SparkLine, VsTarget, seriesColors } from "../charts/BI";
import { MeterBar } from "../charts/MeterBar";
import { percentOf } from "../charts/chart-math";
import "../dashboard/scorecard.css";

type PortfolioProject = {
  id: string; name: string; statuses: Record<string, number>; total: number; open: number;
  done_per_day: { day: string; count: number }[];
  runs_by_agent: Record<string, { total: number; statuses: Record<string, number> }>;
  targets: { target_run_success: number };
};
type PortfolioData = { range: { start: string; end: string }; projects: PortfolioProject[]; totals: { total: number; done: number; open: number } };
const RANGES = [7, 14, 30] as const;
const localDay = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const fmtDay = (day: string) => new Date(day + "T12:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });
const FINISHED = ["Completed", "Failed", "Cancelled"];

/** Each project keeps one color for the whole page, in a stable order (creation order). */
const colorFor = (index: number) => (index < seriesColors.length ? seriesColors[index] : "var(--c-other)");

export function Portfolio({ db, openProject }: { db: Workspace; openProject: (id: string) => void }) {
  const [rangeDays, setRangeDays] = useState<(typeof RANGES)[number]>(7);
  const [data, setData] = useState<PortfolioData | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const end = new Date(); end.setHours(0, 0, 0, 0);
  const start = new Date(end); start.setDate(start.getDate() - (rangeDays - 1));
  const startDay = localDay(start), endDay = localDay(end);

  useEffect(() => {
    let live = true; setError("");
    request<PortfolioData>(`portfolio?start=${startDay}&end=${endDay}&tz_offset=${-new Date().getTimezoneOffset()}`)
      .then(result => { if (live) setData(result); }).catch(err => { if (live) setError(String(err?.message || err)); });
    return () => { live = false; };
  }, [startDay, endDay, db, attempt]);

  const projects = data?.projects || [];
  const color = new Map(projects.map((p, i) => [p.id, colorFor(i)]));
  const days = projects[0]?.done_per_day.map(d => d.day) || [];
  const doneInRange = days.map((_, i) => projects.reduce((s, p) => s + (p.done_per_day[i]?.count || 0), 0));
  const agents = new Map<string, { total: number; ok: number; finished: number }>();
  projects.forEach(p => Object.entries(p.runs_by_agent).forEach(([agent, v]) => {
    const row = agents.get(agent) || { total: 0, ok: 0, finished: 0 };
    row.total += v.total; row.ok += v.statuses.Completed || 0;
    row.finished += FINISHED.reduce((s, k) => s + (v.statuses[k] || 0), 0);
    agents.set(agent, row);
  }));
  const runTotal = [...agents.values()].reduce((s, a) => s + a.total, 0);
  const runOk = [...agents.values()].reduce((s, a) => s + a.ok, 0), runFinished = [...agents.values()].reduce((s, a) => s + a.finished, 0);
  const runTarget = 95; // Agreed default; each project can set its own on the Dashboard.
  const open = [...projects].filter(p => p.open).sort((a, b) => b.open - a.open);
  const biggest = open[0];
  const idle = projects.filter(p => p.total && !p.statuses.Done && !p.statuses["In progress"]);
  const leader = [...projects].sort((a, b) => b.statuses.Done - a.statuses.Done)[0];
  const cumulative = projects.map(p => { let sum = 0; return { name: p.name, color: color.get(p.id)!, values: p.done_per_day.map(d => (sum += d.count)) }; });
  const activeProjects = projects.filter(p => p.done_per_day.some(d => d.count)).length;

  /** Export only when asked: builds a CSV in the browser and downloads it. Nothing is saved to the board. */
  function exportReport() {
    if (!data) return;
    const rows = [["Project", "Done", "In progress", "Blocked", "Planned", "Total", "Open", `Done ${data.range.start} to ${data.range.end}`, "Runs"],
      ...projects.map(p => [p.name, p.statuses.Done, p.statuses["In progress"], p.statuses.Blocked, p.statuses.Planned, p.total, p.open,
        p.done_per_day.reduce((s, d) => s + d.count, 0), Object.values(p.runs_by_agent).reduce((s, a) => s + a.total, 0)])];
    const csv = rows.map(r => r.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const link = Object.assign(document.createElement("a"), { href: url, download: `agentboard-portfolio-${data.range.end}.csv` });
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <div className="v5-dash portfolio">
    <header className="heading">
      <div>
        <h1>Portfolio report</h1>
        <p>{data ? <><b>{data.totals.done}</b> of {data.totals.total} tickets done across {projects.length} projects ({percentOf(data.totals.done, data.totals.total) ?? 0}%).
          {biggest ? <> <b>{biggest.name}</b> holds {percentOf(biggest.open, data.totals.open)}% of open work{idle.some(p => p.id === biggest.id) ? " and hasn't started" : ""}.</> : " No open work."}</>
          : error ? "The portfolio summary is unavailable right now." : "Loading the portfolio…"}</p>
      </div>
      <Button variant="default" size="sm" className="mast-action" leftSection={<Icon page="file" />} disabled={!data} onClick={exportReport}>Export report</Button>
    </header>

    <div className="v5-filters" role="group" aria-label="Report filters">
      <Menu position="bottom-start">
        <Menu.Target><Button variant="default" size="xs" leftSection={<Icon page="calendar" />}>Last {rangeDays} days · {fmtDay(startDay)} – {fmtDay(endDay)} ⌄</Button></Menu.Target>
        <Menu.Dropdown>{RANGES.map(n => <Menu.Item key={n} onClick={() => setRangeDays(n)}>{n === rangeDays ? "✓ " : ""}Last {n} days</Menu.Item>)}</Menu.Dropdown>
      </Menu>
      <span className="v5-filters__note">Read only · {projects.length} projects</span>
    </div>
    {error && <p className="v5-dash__error" role="alert">{error} <button className="link" onClick={() => setAttempt(n => n + 1)}>Retry</button></p>}

    {data && !projects.length ? <p className="cv-empty">No projects yet. Create a project to start the report.</p> : <>
      <section className="v5-kpis" aria-label="Portfolio scorecard">
        <article className="v5-kpi">
          <div className="v5-kpi__label">Portfolio completion</div>
          <Gauge value={data?.totals.done ?? 0} total={data?.totals.total ?? 0} label="Portfolio tickets done" />
          <div className="v5-kpi__foot"><span><b>{data?.totals.done ?? "–"}</b> of {data?.totals.total ?? "–"} tickets done</span><span>No portfolio target; projects set their own</span></div>
        </article>
        <article className="v5-kpi">
          <div className="v5-kpi__label">Run success</div>
          <Gauge value={runOk} total={runFinished} target={runTarget / 100} label="Finished runs completed" />
          <div className="v5-kpi__foot"><span><b>{runOk}</b> of {runFinished} finished runs · {runFinished - runOk} not completed</span><VsTarget actual={percentOf(runOk, runFinished)} target={runTarget} /></div>
        </article>
        <article className="v5-kpi">
          <div className="v5-kpi__label">Done in the last {rangeDays} days</div>
          <div className="v5-kpi__figure">{doneInRange.reduce((a, b) => a + b, 0)}<SparkLine values={doneInRange} label={`Tickets done per day: ${doneInRange.join(", ")}`} /></div>
          <div className="v5-kpi__foot"><span>{activeProjects} of {projects.length} projects delivered</span>{doneInRange.some(Boolean) && <span>Peak {Math.max(...doneInRange)} on {fmtDay(days[doneInRange.indexOf(Math.max(...doneInRange))])}</span>}</div>
        </article>
        <article className="v5-kpi">
          <div className="v5-kpi__label">Open tickets</div>
          <div className="v5-kpi__figure">{data?.totals.open ?? "–"}</div>
          {biggest && <MeterBar value={biggest.open} total={data!.totals.open} tone="neutral" label={`${biggest.name} share of open tickets`} />}
          <div className="v5-kpi__foot"><span>{biggest ? <><b>{biggest.open}</b> in {biggest.name}</> : "Nothing open"}</span>
            <span>{projects.reduce((s, p) => s + (p.statuses.Blocked || 0), 0)} blocked · {projects.reduce((s, p) => s + (p.statuses["In progress"] || 0), 0)} in progress</span></div>
        </article>
      </section>

      <div className="v5-row">
        <ChartCard title="Tickets done, cumulative" insight={leader ? `${leader.name} delivered ${leader.done_per_day.reduce((s, d) => s + d.count, 0)} tickets in this range.${idle.length ? ` ${idle.map(p => p.name).join(", ")} ${idle.length === 1 ? "has" : "have"} not started.` : ""}` : undefined}
          table={<DataTable head={["Day", ...projects.map(p => p.name)]} rows={days.map((d, i) => [fmtDay(d), ...cumulative.map(c => c.values[i])])} />}>
          <DailyLines days={days} series={cumulative} label="Cumulative tickets done per project" />
        </ChartCard>
        <ChartCard title="Where the open work sits" insight={biggest ? `${biggest.name}: ${biggest.open} of ${data?.totals.open} open tickets.` : "No open work."}
          table={<DataTable head={["Project", "Open", "Share"]} rows={open.map(p => [p.name, p.open, `${percentOf(p.open, data?.totals.open || 0)}%`])} />}>
          <Pie parts={open.map(p => ({ name: p.name, value: p.open, color: color.get(p.id)!, sub: p.statuses.Done ? `${p.statuses.Done} of ${p.total} done` : "Not started" }))} label="Open tickets by project" />
        </ChartCard>
      </div>

      <div className="v5-row v5-row--even">
        <ChartCard title="Project completion" insight={`${projects.filter(p => p.total && p.statuses.Done === p.total).length} of ${projects.length} projects are complete.`}
          table={<DataTable head={["Project", "Done", "Total", "Completion"]} rows={projects.map(p => [p.name, p.statuses.Done, p.total, `${percentOf(p.statuses.Done, p.total) ?? 0}%`])} />}>
          <MeterList rows={[...projects].sort((a, b) => (percentOf(b.statuses.Done, b.total) ?? -1) - (percentOf(a.statuses.Done, a.total) ?? -1)).map(p => ({
            key: p.name, swatch: color.get(p.id), name: <button className="link" onClick={() => openProject(p.id)}>{p.name}</button>,
            value: p.statuses.Done, total: p.total, tone: p.total && p.statuses.Done === p.total ? "good" as const : "violet" as const,
            figure: p.total ? `${percentOf(p.statuses.Done, p.total)}%` : "–", sub: `${p.statuses.Done} of ${p.total}` }))} />
        </ChartCard>
        <ChartCard title="Runs by agent" insight={runTotal ? `${[...agents].sort((a, b) => b[1].total - a[1].total)[0][0]} reported ${percentOf([...agents].sort((a, b) => b[1].total - a[1].total)[0][1].total, runTotal)}% of runs.` : "No runs reported yet."}
          table={<DataTable head={["Agent", "Runs", "Completed", "Finished"]} rows={[...agents].map(([a, v]) => [a, v.total, v.ok, v.finished])} />}>
          <MeterList rows={[...agents].sort((a, b) => b[1].total - a[1].total).map(([agent, v]) => ({
            key: agent, name: agent, value: v.total, total: runTotal, tone: "violet" as const, figure: v.total, sub: v.finished ? `${percentOf(v.ok, v.finished)}% completed` : "None finished" }))} />
        </ChartCard>
      </div>
    </>}
  </div>;
}
