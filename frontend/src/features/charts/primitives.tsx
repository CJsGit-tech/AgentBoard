// Small V5 chart primitives. Colors come from the validated palette in v5.css.
import "./charts.css";

export const statusOrder = ["Done", "In progress", "Blocked", "Planned"] as const;
export type Status = (typeof statusOrder)[number];
export const statusFill: Record<Status, string> = {
  Done: "var(--c-done)", "In progress": "var(--c-progress)", Blocked: "var(--c-blocked)", Planned: "var(--c-planned)",
};
export const statusShape: Record<Status, string> = { Done: "✓", "In progress": "◐", Blocked: "◆", Planned: "○" };

/** Thin segmented bar for one whole split by ticket status. */
export function StatusBar({ counts, label, height = 8 }: { counts: Record<string, number>; label: string; height?: number }) {
  const parts = statusOrder.map(status => ({ status, n: counts[status] || 0 })).filter(part => part.n > 0);
  const total = parts.reduce((sum, part) => sum + part.n, 0);
  const text = total ? statusOrder.map(status => `${counts[status] || 0} ${status}`).join(", ") : "No tickets yet";
  return (
    <div className="cv-seg" style={{ height }} role="img" aria-label={`${label}: ${text}`}>
      {total ? parts.map(part => (
        <span key={part.status} className="cv-seg__part" style={{ flexGrow: part.n, background: statusFill[part.status] }}
          title={`${part.status}: ${part.n} of ${total}`} />
      )) : <span className="cv-seg__empty" />}
    </div>
  );
}

/** Seven columns, today last in violet; zero days draw only the baseline. */
export function SparkColumns({ values, label, height = 26 }: { values: number[]; label: string; height?: number }) {
  const max = Math.max(1, ...values), bar = 6, gap = 3, width = values.length * (bar + gap) - gap;
  return (
    <svg className="cv-spark" width={width} height={height} role="img" aria-label={`${label}: ${values.join(", ")}`}>
      <line x1={0} x2={width} y1={height - .5} y2={height - .5} className="cv-axis" />
      {values.map((value, i) => {
        const h = value ? Math.max(2, (value / max) * (height - 3)) : 0;
        return <rect key={i} x={i * (bar + gap)} y={height - 1 - h} width={bar} height={h} rx={1.5}
          className={i === values.length - 1 ? "cv-spark__now" : "cv-spark__bar"} />;
      })}
    </svg>
  );
}

export function Legend({ items }: { items: { label: string; color: string; shape?: string }[] }) {
  return (
    <ul className="cv-legend">
      {items.map(item => (
        <li key={item.label}>
          <span className="cv-key-dot" style={{ background: item.color }} />
          {item.shape ? <span aria-hidden="true" className="cv-legend__shape">{item.shape}</span> : null}
          <span>{item.label}</span>
        </li>
      ))}
    </ul>
  );
}

export const StatusLegend = () => <Legend items={statusOrder.map(status => ({ label: status, color: statusFill[status], shape: statusShape[status] }))} />;

/** Counts per local calendar day for the last `days` days, today last. */
export function perDay(times: string[], days = 7, now = new Date()) {
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - (days - 1)).getTime();
  const counts = Array<number>(days).fill(0);
  for (const time of times) {
    const at = new Date(time);
    const day = Math.floor((new Date(at.getFullYear(), at.getMonth(), at.getDate()).getTime() - start) / 86400000);
    if (day >= 0 && day < days) counts[day]++;
  }
  return counts;
}

export function ago(time: string | null | undefined, now = Date.now()) {
  if (!time) return "No activity yet";
  const minutes = Math.max(0, Math.round((now - Date.parse(time)) / 60000));
  if (minutes < 1) return "Active just now";
  if (minutes < 60) return `Active ${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return hours < 24 ? `Active ${hours} h ago` : `Active ${Math.round(hours / 24)} d ago`;
}
