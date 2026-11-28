// One lane per agent, one dot per run on a shared time axis, colored by run status.
import { useLayoutEffect, useRef, useState } from "react";
import type { Row } from "../../model";
import { Legend } from "./primitives";

export const runFill: Record<string, string> = {
  Completed: "var(--c-done)", Running: "var(--c-progress)", Queued: "var(--c-planned)", "Waiting for input": "var(--c-blocked)",
  Blocked: "var(--c-blocked)", Failed: "var(--c-failed)", Cancelled: "var(--c-other)",
};
const runShape: Record<string, string> = { Completed: "✓", Running: "◐", Queued: "○", "Waiting for input": "◆", Blocked: "◆", Failed: "!", Cancelled: "×" };
const DAY = 86400000;

export function RunSwimlane({ runs, selected, onPick }: { runs: Row[]; selected?: string; onPick: (run: Row) => void }) {
  const box = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);
  useLayoutEffect(() => {
    const el = box.current; if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(280, Math.floor(e.contentRect.width))));
    ro.observe(el); return () => ro.disconnect();
  }, []);
  const timed = runs.filter(run => Date.parse(run.updated || ""));
  if (!timed.length) return null;
  const agents = [...new Set(timed.map(run => run.agent || "Not recorded"))]
    .sort((a, b) => timed.filter(r => (r.agent || "Not recorded") === b).length - timed.filter(r => (r.agent || "Not recorded") === a).length);
  const times = timed.map(run => Date.parse(run.updated!));
  const start = new Date(Math.min(...times)); start.setHours(0, 0, 0, 0);
  const end = new Date(Math.max(...times)); end.setHours(24, 0, 0, 0);
  const narrow = width < 520;
  const P = { l: narrow ? 44 : 150, r: 56, t: 8, b: 26 }, lane = 34;
  const iw = width - P.l - P.r, height = P.t + agents.length * lane + P.b;
  const x = (t: number) => P.l + ((t - start.getTime()) / (end.getTime() - start.getTime())) * iw;
  const days = Math.round((end.getTime() - start.getTime()) / DAY);
  const maxTicks = narrow ? 4 : 8;
  const ticks = Array.from({ length: days + 1 }, (_, i) => start.getTime() + i * DAY).filter((_, i, all) => all.length <= maxTicks + 1 || i % Math.ceil(all.length / maxTicks) === 0);
  // Short labels must stay distinct (Codex and Claude both start with C).
  const initials = (name: string) => name.split(/\s+/).map(w => w[0]).join("").toUpperCase();
  const short = (name: string) => agents.filter(a => initials(a) === initials(name)).length > 1 ? name.slice(0, 2) : initials(name);
  const present = [...new Set(timed.map(run => run.status || ""))].filter(status => runFill[status]);
  return (
    <figure className="cv-swim" ref={box}>
      <svg width={width} height={height} role="group" aria-label={`Runs by agent over time: ${agents.map(a => `${a} ${timed.filter(r => (r.agent || "Not recorded") === a).length}`).join(", ")}`}>
        {ticks.map(t => <g key={t}>
          <line x1={x(t)} x2={x(t)} y1={P.t} y2={height - P.b} className="cv-grid" />
          <text x={x(t)} y={height - 8} textAnchor="middle" className="cv-tick">{new Date(t).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</text>
        </g>)}
        {agents.map((agent, i) => {
          const y = P.t + i * lane + lane / 2;
          const mine = timed.filter(run => (run.agent || "Not recorded") === agent);
          return <g key={agent}>
            <line x1={P.l} x2={P.l + iw} y1={y} y2={y} className="cv-axis" />
            <text x={P.l - 10} y={y + 4} textAnchor="end" className="cv-rowlabel">{narrow ? short(agent) : agent}</text>
            <text x={P.l + iw + 10} y={y + 4} className="cv-value">{mine.length}</text>
            {mine.map(run => {
              const active = run.id === selected;
              return <circle key={run.id} cx={x(Date.parse(run.updated!))} cy={y} r={active ? 7 : 5} className={"cv-swim__dot" + (active ? " is-active" : "")}
                style={{ fill: runFill[run.status || ""] || "var(--c-other)" }} tabIndex={0} role="button"
                aria-label={`${run.name}. ${run.status}. ${agent}. ${new Date(run.updated!).toLocaleString()}`}
                onClick={() => onPick(run)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onPick(run); } }}>
                <title>{`${run.name}\n${run.status} · ${new Date(run.updated!).toLocaleString()}`}</title>
              </circle>;
            })}
          </g>;
        })}
      </svg>
      <figcaption><Legend items={present.map(status => ({ label: status, color: runFill[status], shape: runShape[status] }))} /></figcaption>
    </figure>
  );
}
