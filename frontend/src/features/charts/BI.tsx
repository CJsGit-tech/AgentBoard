// Design Profile V5 business-intelligence charts. Palette and specs: DESIGN.md rev 15.
import { useLayoutEffect, useRef, useState, type KeyboardEvent, type PointerEvent, type ReactNode } from "react";
import { SegmentedControl } from "@mantine/core";
import { axisTicks, burnupSteps, gaugeGeometry, linePath, nearestIndex, percentOf, pieSlices, spreadLabels, versusTarget } from "./chart-math";
import { Legend } from "./primitives";
import { MeterBar } from "./MeterBar";
import "./charts.css";

export const seriesColors = ["var(--c-s1)", "var(--c-s2)", "var(--c-s3)", "var(--c-s4)"];
const DARK_FILLS = new Set(["var(--c-s1)", "var(--c-done)", "var(--c-progress)"]);

function useWidth<T extends HTMLElement>(fallback = 600) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(fallback);
  useLayoutEffect(() => {
    const el = ref.current; if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(Math.max(200, Math.floor(entry.contentRect.width))));
    ro.observe(el); return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}

/** A chart with a title, a one-sentence finding, optional tools and a Chart | Table switch. */
export function ChartCard({ title, insight, table, tools, children, className = "" }: { title: string; insight?: ReactNode; table?: ReactNode; tools?: ReactNode; children: ReactNode; className?: string }) {
  const [mode, setMode] = useState("Chart");
  return (
    <figure className={"cv-card " + className} aria-label={title}>
      <header className="cv-card__head">
        <div><h2 className="cv-card__title">{title}</h2>{insight ? <p className="cv-card__insight">{insight}</p> : null}</div>
        <div className="cv-card__tools">{tools}{table ? <SegmentedControl size="xs" radius="xl" value={mode} onChange={setMode} data={["Chart", "Table"]} aria-label={title + " view"} /> : null}</div>
      </header>
      {mode === "Table" && table ? <div className="cv-table-wrap">{table}</div> : children}
    </figure>
  );
}

export function DataTable({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
  return <table className="cv-table"><thead><tr>{head.map(h => <th key={h} scope="col">{h}</th>)}</tr></thead>
    <tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => j ? <td key={j}>{cell}</td> : <th key={j} scope="row">{cell}</th>)}</tr>)}</tbody></table>;
}

type Tip = { x: number; y: number; body: ReactNode } | null;
function TipBox({ tip, width }: { tip: Tip; width: number }) {
  if (!tip) return null;
  return <div className="cv-tip" role="status" style={{ left: Math.min(Math.max(8, tip.x + 14), width - 220), top: Math.max(0, tip.y - 12) }}>{tip.body}</div>;
}
export function TipRow({ color, value, label }: { color?: string; value: ReactNode; label: ReactNode }) {
  return <div className="cv-tip__row">{color ? <span className="cv-key-line" style={{ background: color }} /> : null}<b>{value}</b><span>{label}</span></div>;
}
const localPoint = (e: PointerEvent<Element>, box: HTMLElement) => {
  const r = box.getBoundingClientRect(); const k = r.width / box.offsetWidth || 1;
  return { x: (e.clientX - r.left) / k, y: (e.clientY - r.top) / k };
};

/* ---------- target comparison ---------- */
export function VsTarget({ actual, target, lowerIsBetter, unit = "%" }: { actual: number | null; target: number; lowerIsBetter?: boolean; unit?: string }) {
  const { met, gap } = versusTarget(actual, target, lowerIsBetter);
  if (met === null || gap === null) return <span className="bi-vs is-none">No data yet<span className="bi-vs__t"> · target {lowerIsBetter ? "≤ " : ""}{target}{unit}</span></span>;
  const size = Math.abs(gap);
  const words = size < 0.005 ? "On target" : lowerIsBetter ? (met ? "Within target" : `${size}${unit === "%" ? " pts" : " " + unit.trim()} over target`)
    : met ? `${size} ${size === 1 ? "pt" : "pts"} above target` : `${size} ${size === 1 ? "pt" : "pts"} below target`;
  return <span className={"bi-vs " + (met ? "is-good" : "is-warn")}><span aria-hidden="true">{met ? "✓" : "◆"}</span> {words}
    <span className="bi-vs__t"> · target {lowerIsBetter ? "≤ " : ""}{target}{unit}</span></span>;
}

/* ---------- gauge: one ratio against a target ---------- */
export function Gauge({ value, total, target, label, size = 148 }: { value: number; total: number; target?: number; label: string; size?: number }) {
  const pct = percentOf(value, total);
  const fraction = total ? value / total : 0;
  const geo = gaugeGeometry(fraction, size, 12, target);
  const tone = pct === null ? "neutral" : target === undefined ? "violet" : fraction >= target - 1e-9 ? "good" : "warn";
  const text = pct === null ? "No data yet" : `${pct}%${target !== undefined ? `, target ${Math.round(target * 100)}%` : ""}`;
  return (
    <svg className={"bi-gauge is-" + tone} width={size} height={geo.height} viewBox={`0 0 ${size} ${geo.height}`} role="meter"
      aria-label={label} aria-valuemin={0} aria-valuemax={total || 1} aria-valuenow={value} aria-valuetext={text} tabIndex={0}>
      <title>{`${label}: ${total ? `${value} of ${total}` : "no data"} · ${text}`}</title>
      <path d={geo.track} className="bi-gauge__track" strokeWidth={12} />
      {geo.fill ? <path d={geo.fill} className="bi-gauge__fill" strokeWidth={12} /> : null}
      {geo.tick ? <line x1={geo.tick.from[0]} y1={geo.tick.from[1]} x2={geo.tick.to[0]} y2={geo.tick.to[1]} className="bi-gauge__target" /> : null}
      <text x={geo.cx} y={geo.cy - 4} textAnchor="middle" className="bi-gauge__value">{pct === null ? "–" : pct}{pct === null ? null : <tspan className="bi-gauge__unit">%</tspan>}</text>
    </svg>
  );
}

/* ---------- meter list: one ratio per named row ---------- */
export function MeterList({ rows }: { rows: { key: string; name: ReactNode; value: number; total: number; target?: number; tone?: "good" | "warn" | "violet" | "neutral"; figure: ReactNode; sub?: ReactNode; swatch?: string }[] }) {
  if (!rows.length) return <p className="cv-empty">No rows yet.</p>;
  return <ul className="bi-meterlist">{rows.map(r => (
    <li key={r.key}>
      <div className="bi-meterlist__name">{r.swatch ? <span className="cv-key-dot" style={{ background: r.swatch }} /> : null}<span>{r.name}</span></div>
      <MeterBar value={r.value} total={r.total} target={r.target} tone={r.tone} label={r.key} />
      <div className="bi-meterlist__fig"><b>{r.figure}</b>{r.sub ? <span>{r.sub}</span> : null}</div>
    </li>
  ))}</ul>;
}

/* ---------- pie: one whole, 3–4 clearly unequal parts ---------- */
export function Pie({ parts, label, unit = "tickets", size = 156 }: { parts: { name: string; value: number; color: string; sub?: string }[]; label: string; unit?: string; size?: number }) {
  const [hover, setHover] = useState<number | null>(null);
  const r = size / 2 - 6;
  const slices = pieSlices(parts, r, size / 2, size / 2).map(s => ({ ...s, color: parts.find(p => p.name === s.name)!.color, sub: parts.find(p => p.name === s.name)!.sub }));
  if (!slices.length) return <p className="cv-empty">No {unit} yet.</p>;
  const shift = (i: number, mid: number) => hover === i ? [Math.cos(mid) * 4, Math.sin(mid) * 4] : [0, 0];
  return (
    <div className="bi-pie">
      <svg width={size} height={size} role="img" aria-label={`${label}: ${slices.map(s => `${s.name} ${s.value} (${s.percent}%)`).join(", ")}`} className="bi-pie__svg">
        {slices.map((s, i) => { const [dx, dy] = shift(i, s.mid); return <path key={s.name} d={s.path} fill={s.color} transform={`translate(${dx},${dy})`}
          className={"bi-pie__slice" + (hover !== null && hover !== i ? " is-dim" : "")} onPointerEnter={() => setHover(i)} onPointerLeave={() => setHover(null)}><title>{`${s.name}: ${s.value} ${unit} (${s.percent}%)`}</title></path>; })}
        {slices.map((s, i) => { if (s.share < 0.12) return null; const [dx, dy] = shift(i, s.mid); const rr = r * (s.share > 0.6 ? 0.42 : 0.62);
          return <text key={s.name} x={size / 2 + Math.cos(s.mid) * rr + dx} y={size / 2 + Math.sin(s.mid) * rr + dy + 4} textAnchor="middle"
            className={"bi-pie__pct" + (DARK_FILLS.has(s.color) ? " is-light" : "")}>{s.percent}%</text>; })}
      </svg>
      <ul className="bi-pie__legend">{slices.map((s, i) => (
        <li key={s.name}><button type="button" className={hover === i ? "is-active" : ""} onPointerEnter={() => setHover(i)} onPointerLeave={() => setHover(null)}
          onFocus={() => setHover(i)} onBlur={() => setHover(null)} aria-label={`${s.name}: ${s.value} ${unit}, ${s.percent}%`}>
          <span className="cv-key-dot" style={{ background: s.color }} /><span className="bi-pie__name">{s.name}{s.sub ? <small>{s.sub}</small> : null}</span>
          <b>{s.value}</b><span className="bi-pie__share">{s.percent}%</span>
        </button></li>
      ))}</ul>
    </div>
  );
}

/* ---------- daily lines with crosshair ---------- */
export type Series = { name: string; color: string; values: (number | null)[] };
export function DailyLines({ days, series, label, height = 230, max, format = (v: number) => String(v), reference }: {
  days: string[]; series: Series[]; label: string; height?: number; max?: number; format?: (v: number) => string; reference?: { value: number; label: string };
}) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const [hi, setHi] = useState<number | null>(null);
  const [tip, setTip] = useState<Tip>(null);
  const narrow = W < 520;
  const P = { l: 40, r: narrow ? 16 : 132, t: 14, b: 28 };
  const iw = W - P.l - P.r, ih = height - P.t - P.b;
  const { top, ticks } = axisTicks([...series.flatMap(s => s.values), reference?.value ?? null], max);
  const x = (i: number) => P.l + (days.length > 1 ? (i / (days.length - 1)) * iw : iw / 2);
  const y = (v: number) => P.t + ih - (v / top) * ih;
  const dayName = (d: string) => new Date(d + "T12:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });
  const lastY = series.map(s => y([...s.values].reverse().find(v => v !== null) ?? 0));
  const labelY = spreadLabels(lastY);
  const show = (i: number, px: number, py: number) => {
    setHi(i);
    setTip({ x: px, y: py, body: <><div className="cv-tip__head">{dayName(days[i])}</div>
      {[...series].sort((a, b) => (b.values[i] ?? -1) - (a.values[i] ?? -1)).map(s => <TipRow key={s.name} color={s.color} value={s.values[i] === null ? "–" : format(s.values[i]!)} label={s.name} />)}</> });
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight" && e.key !== "Home" && e.key !== "End") return;
    e.preventDefault();
    const i = e.key === "Home" ? 0 : e.key === "End" ? days.length - 1 : Math.max(0, Math.min(days.length - 1, (hi ?? days.length) + (e.key === "ArrowRight" ? 1 : -1)));
    show(i, x(i), P.t + 20);
  };
  return (
    <div ref={ref} className="cv-plot" style={{ height }}
      onPointerMove={e => { const p = localPoint(e, ref.current!); if (p.x >= P.l - 10 && p.x <= P.l + iw + 10) { const i = nearestIndex(p.x, P.l, iw, days.length); show(i, x(i), p.y); } }}
      onPointerLeave={() => { setHi(null); setTip(null); }}>
      <svg width={W} height={height} tabIndex={0} role="img" aria-label={`${label}. Use the left and right arrow keys to read each day.`} onKeyDown={onKey} onBlur={() => { setHi(null); setTip(null); }}>
        {ticks.map(t => <g key={t}><line x1={P.l} x2={P.l + iw} y1={y(t)} y2={y(t)} className={t === 0 ? "cv-axis" : "cv-grid"} /><text x={P.l - 8} y={y(t) + 4} textAnchor="end" className="cv-tick">{format(t)}</text></g>)}
        {days.map((d, i) => (narrow && days.length > 4 && i % 2 ? null : <text key={d} x={x(i)} y={height - 8} textAnchor="middle" className="cv-tick">{dayName(d)}</text>))}
        {reference ? <g><line x1={P.l} x2={P.l + iw} y1={y(reference.value)} y2={y(reference.value)} className="bi-ref" /><text x={P.l + 6} y={y(reference.value) - 6} className="bi-ref__label">{reference.label}</text></g> : null}
        {hi !== null ? <line x1={x(hi)} x2={x(hi)} y1={P.t} y2={P.t + ih} className="cv-cross" /> : null}
        {series.map(s => <path key={s.name} d={linePath(s.values, x, y)} className="cv-line" style={{ stroke: s.color }} />)}
        {series.map(s => { const i = hi ?? s.values.length - 1; const v = s.values[i]; return v === null || v === undefined ? null : <circle key={s.name} cx={x(i)} cy={y(v)} r={4.5} className="cv-dot" style={{ fill: s.color }} />; })}
        {!narrow ? series.map((s, k) => { const v = [...s.values].reverse().find(n => n !== null); return v === undefined || v === null ? null :
          <text key={s.name} x={P.l + iw + 10} y={labelY[k] + 4} className="cv-endlabel"><tspan>{format(v)}</tspan><tspan dx={6} className="cv-endlabel--muted">{s.name}</tspan></text>; }) : null}
      </svg>
      <TipBox tip={tip} width={W} />
    </div>
  );
}

/** Tiny line for a KPI tile; gaps where there is no value, optional target line. */
export function SparkLine({ values, label, width = 96, height = 30, target }: { values: (number | null)[]; label: string; width?: number; height?: number; target?: number }) {
  const nums = values.filter((v): v is number => v !== null);
  const top = (Math.max(0, ...nums, target ?? 0) * 1.1) || 1;
  const x = (i: number) => 3 + (values.length > 1 ? (i / (values.length - 1)) * (width - 6) : (width - 6) / 2);
  const y = (v: number) => height - 3 - (v / top) * (height - 6);
  const lastIndex = values.map((v, i) => (v === null ? -1 : i)).filter(i => i >= 0).pop();
  return (
    <svg width={width} height={height} className="bi-spark" role="img" aria-label={label}>
      {target !== undefined ? <line x1={0} x2={width} y1={y(target)} y2={y(target)} className="bi-ref" /> : null}
      <path d={linePath(values, x, y)} className="cv-line" style={{ stroke: "var(--c-s1)" }} />
      {lastIndex !== undefined ? <circle cx={x(lastIndex)} cy={y(values[lastIndex]!)} r={3.5} className="cv-dot" style={{ fill: "var(--c-s1)" }} /> : null}
    </svg>
  );
}

/* ---------- burn-up: cumulative scope against done ---------- */
export function BurnUp({ tickets, start, end, pins = [], height = 260, label }: {
  tickets: { created: number; done: number | null }[]; start: number; end: number; pins?: { at: number; name: string; done: boolean }[]; height?: number; label: string;
}) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const [cursor, setCursor] = useState<number | null>(null);
  const [tip, setTip] = useState<Tip>(null);
  const steps = burnupSteps(tickets, start, end);
  const narrow = W < 520;
  const P = { l: 36, r: narrow ? 16 : 64, t: 12, b: pins.length && !narrow ? 50 : 30 };
  const iw = W - P.l - P.r, ih = height - P.t - P.b;
  const { top, ticks } = axisTicks(steps.map(s => s.scope));
  const x = (t: number) => P.l + ((t - start) / Math.max(1, end - start)) * iw;
  const y = (v: number) => P.t + ih - (v / top) * ih;
  const path = (k: "scope" | "done") => steps.map((s, i) => (i ? `H${x(s.at).toFixed(1)}V${y(s[k]).toFixed(1)}` : `M${x(s.at).toFixed(1)},${y(s[k]).toFixed(1)}`)).join("");
  const at = (t: number) => [...steps].reverse().find(s => s.at <= t) ?? steps[0];
  const show = (t: number, px: number, py: number) => {
    const s = at(t); setCursor(t);
    setTip({ x: px, y: py, body: <><div className="cv-tip__head">{new Date(t).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</div>
      <TipRow color="var(--c-s1)" value={s.done} label="done" /><TipRow color="var(--c-scope)" value={s.scope} label="in scope" /><TipRow value={s.scope - s.done} label="remaining" /></> });
  };
  const dayTicks: number[] = []; for (let d = new Date(start); d.getTime() <= end; d.setDate(d.getDate() + 1)) dayTicks.push(d.getTime());
  const shownTicks = dayTicks.filter((_, i, all) => all.length <= (narrow ? 4 : 8) || i % Math.ceil(all.length / (narrow ? 4 : 8)) === 0);
  const last = steps[steps.length - 1];
  return (
    <div ref={ref} className="cv-plot" style={{ height }}
      onPointerMove={e => { const p = localPoint(e, ref.current!); if (p.x >= P.l && p.x <= P.l + iw) show(start + ((p.x - P.l) / iw) * (end - start), p.x, p.y); }}
      onPointerLeave={() => { setCursor(null); setTip(null); }}>
      <svg width={W} height={height} tabIndex={0} role="img" aria-label={`${label}: ${last.done} of ${last.scope} done at the end of the range. Use the arrow keys to step through changes.`}
        onKeyDown={e => {
          if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return; e.preventDefault();
          const cur = cursor === null ? steps.length - 1 : steps.findIndex(s => s.at >= cursor);
          const i = Math.max(0, Math.min(steps.length - 1, (cur < 0 ? steps.length - 1 : cur) + (e.key === "ArrowRight" ? 1 : -1)));
          show(steps[i].at, x(steps[i].at), y(steps[i].done));
        }} onBlur={() => { setCursor(null); setTip(null); }}>
        {ticks.map(t => <g key={t}><line x1={P.l} x2={P.l + iw} y1={y(t)} y2={y(t)} className={t === 0 ? "cv-axis" : "cv-grid"} /><text x={P.l - 8} y={y(t) + 4} textAnchor="end" className="cv-tick">{t}</text></g>)}
        {shownTicks.map(t => <text key={t} x={x(t)} y={P.t + ih + 16} textAnchor="middle" className="cv-tick">{new Date(t).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</text>)}
        <path d={path("done") + `V${y(0)}H${x(steps[0].at)}Z`} className="cv-area" />
        <path d={path("scope")} className="cv-line cv-line--scope" />
        <path d={path("done")} className="cv-line cv-line--done" />
        {!narrow ? pins.map(pin => <g key={pin.name + pin.at}><line x1={x(pin.at)} x2={x(pin.at)} y1={P.t} y2={P.t + ih} className="cv-grid" />
          <circle cx={x(pin.at)} cy={P.t + ih + 30} r={4} className={pin.done ? "cv-pin__done" : "cv-pin__open"}><title>{pin.name}</title></circle></g>) : null}
        {cursor !== null ? <line x1={x(cursor)} x2={x(cursor)} y1={P.t} y2={P.t + ih} className="cv-cross" /> : null}
        {!narrow ? <text x={x(last.at) + 8} y={y(last.done) + 4} className="cv-endlabel">{last.done} done</text> : null}
      </svg>
      <TipBox tip={tip} width={W} />
      <Legend items={[{ label: "Done", color: "var(--c-s1)" }, { label: "In scope", color: "var(--c-scope)" }]} />
    </div>
  );
}
