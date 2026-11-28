// Linear meter: a fill on a lighter track of the same hue, with an optional target tick.
export function MeterBar({ value, total, target, tone, label }: { value: number; total: number; target?: number; tone?: "good" | "warn" | "violet" | "neutral"; label: string }) {
  const f = total ? Math.min(1, value / total) : 0;
  const t = tone ?? (target === undefined ? "violet" : f >= target - 1e-9 ? "good" : "warn");
  return (
    <div className={"bi-meter is-" + t} role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={total} aria-valuenow={value}
      aria-valuetext={`${value} of ${total}${target !== undefined ? `, target ${Math.round(target * 100)}%` : ""}`}>
      <div className="bi-meter__fill" style={{ width: `${f * 100}%` }} />
      {target !== undefined && target < 1 ? <i className="bi-meter__target" style={{ left: `${target * 100}%` }} /> : null}
    </div>
  );
}
