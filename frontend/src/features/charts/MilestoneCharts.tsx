// Milestones page charts (Design Profile V5, Frame 6): timeline and time-to-last-update bead plot.
import { useLayoutEffect, useRef, useState } from "react";
import { beadGroups, logPosition, medianOf } from "./chart-math";

function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(800);
  useLayoutEffect(() => {
    const el = ref.current; if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(240, Math.floor(e.contentRect.width))));
    ro.observe(el); return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}
const hours = (h: number) => (h < 1 ? `${Math.round(h * 60)} min` : `${h.toFixed(h < 10 ? 1 : 0)} h`);
const stamp = (t: number) => new Date(t).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });

export type MilestoneSpan = { id: string; name: string; start: number; end: number; done: number; total: number; median: number | null };

/** Each bar runs from the first ticket filed to the last update; the fill is the done share. */
export function MilestoneTimeline({ spans, onOpen }: { spans: MilestoneSpan[]; onOpen?: (id: string) => void }) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const rows = spans.filter(s => s.total && Number.isFinite(s.start) && Number.isFinite(s.end));
  if (!rows.length) return <p className="cv-empty">No milestone has tickets yet.</p>;
  const narrow = W < 560;
  const t0 = Math.min(...rows.map(r => r.start)), t1 = Math.max(...rows.map(r => r.end), t0 + 3600e3);
  const P = { l: narrow ? 8 : 230, r: 64, t: 6, b: 26 }, lane = narrow ? 46 : 32;
  const iw = W - P.l - P.r, height = P.t + rows.length * lane + P.b;
  const x = (t: number) => P.l + ((t - t0) / (t1 - t0)) * iw;
  const day = 86400e3, first = new Date(t0); first.setHours(0, 0, 0, 0);
  const ticks: number[] = []; for (let t = first.getTime(); t <= t1; t += day) if (t >= t0 - day / 2) ticks.push(t);
  const shown = ticks.filter((_, i) => ticks.length <= (narrow ? 4 : 8) || i % Math.ceil(ticks.length / (narrow ? 4 : 8)) === 0);
  return (
    <div ref={ref} className="cv-plot">
      <svg width={W} height={height} role="list" aria-label="Milestone timeline">
        {shown.map(t => <g key={t}><line x1={x(t)} x2={x(t)} y1={P.t} y2={height - P.b} className="cv-grid" />
          <text x={x(t)} y={height - 8} textAnchor="middle" className="cv-tick">{new Date(t).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</text></g>)}
        {rows.map((r, i) => {
          const y = P.t + i * lane + (narrow ? 22 : 8), w = Math.max(4, x(r.end) - x(r.start)), share = r.done / r.total;
          const label = `${r.name}: ${stamp(r.start)} to ${stamp(r.end)}, ${r.done} of ${r.total} done${r.median !== null ? `, median ${hours(r.median)}` : ""}`;
          return <g key={r.id} role="listitem" aria-label={label} tabIndex={0} className="cv-gantt__row"
            onClick={() => onOpen?.(r.id)} onKeyDown={e => { if (e.key === "Enter") onOpen?.(r.id); }}>
            <title>{label}</title>
            <text x={narrow ? P.l : P.l - 12} y={narrow ? y - 6 : y + 12} textAnchor={narrow ? "start" : "end"} className="cv-rowlabel">{narrow && r.name.length > 34 ? r.name.slice(0, 33) + "…" : r.name.length > 32 && !narrow ? r.name.slice(0, 31) + "…" : r.name}</text>
            <rect x={x(r.start)} y={y} width={w} height={16} rx={4} className="cv-gantt__track" />
            {share > 0 && <rect x={x(r.start)} y={y} width={Math.max(3, w * share)} height={16} rx={4} className={share === 1 ? "cv-gantt__done" : "cv-gantt__part"} />}
            <text x={x(r.start) + w + 8} y={y + 12} className="cv-value">{r.done}/{r.total}</text>
          </g>;
        })}
      </svg>
    </div>
  );
}

/** Log-scale bead plot of hours from filing to last update; batches become one bead with a count. */
export function LeadBeads({ rows }: { rows: { name: string; hours: number[] }[] }) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const usable = rows.filter(r => r.hours.length);
  if (!usable.length) return <p className="cv-empty">No done tickets yet.</p>;
  const narrow = W < 560;
  const MIN = 1 / 12, MAX = Math.max(16, ...usable.flatMap(r => r.hours));
  const P = { l: narrow ? 8 : 230, r: narrow ? 56 : 90, t: 8, b: 26 }, lane = narrow ? 50 : 36;
  const iw = W - P.l - P.r, height = P.t + usable.length * lane + P.b;
  const x = (h: number) => P.l + logPosition(h, MIN, MAX) * iw;
  const ticks = [5 / 60, 0.25, 1, 4, 16, 64, 256].filter(t => t <= MAX * 1.01);
  return (
    <div ref={ref} className="cv-plot">
      <svg width={W} height={height} role="list" aria-label="Time from filing to last update by milestone, log scale">
        {ticks.map(t => <g key={t}><line x1={x(t)} x2={x(t)} y1={P.t} y2={height - P.b} className="cv-grid" /><text x={x(t)} y={height - 8} textAnchor="middle" className="cv-tick">{hours(t)}</text></g>)}
        {usable.map((r, i) => {
          const y = P.t + i * lane + (narrow ? 30 : 18), beads = beadGroups(r.hours), med = medianOf(r.hours)!;
          return <g key={r.name} role="listitem" aria-label={`${r.name}: ${r.hours.length} done tickets, median ${hours(med)}, ${beads.filter(b => b.count > 1).map(b => `${b.count} at ${hours(b.value)}`).join(", ") || "no batches"}`}>
            <text x={narrow ? P.l : P.l - 12} y={narrow ? y - 14 : y + 4} textAnchor={narrow ? "start" : "end"} className="cv-rowlabel">{r.name.length > 34 ? r.name.slice(0, 33) + "…" : r.name}</text>
            <line x1={P.l} x2={P.l + iw} y1={y} y2={y} className="cv-axis" />
            {beads.map(b => { const radius = Math.min(11, 4 + Math.sqrt(b.count) * 1.6); return <g key={b.value}>
              <circle cx={x(b.value)} cy={y} r={radius} className="cv-bead"><title>{`${b.count} ticket${b.count > 1 ? "s" : ""} · ${hours(b.value)} to last update`}</title></circle>
              {b.count > 1 && <text x={x(b.value)} y={y - radius - 3} textAnchor="middle" className="cv-count">{b.count}</text>}</g>; })}
            <line x1={x(med)} x2={x(med)} y1={y - 10} y2={y + 10} className="cv-median" />
            <text x={P.l + iw + 10} y={y + 4} className="cv-value">{hours(med)}</text>
          </g>;
        })}
      </svg>
    </div>
  );
}
