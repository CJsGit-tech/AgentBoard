// Pure geometry and number helpers for the V5 charts. No imports, so tests can transpile it alone.

export type Ratio = { value: number; total: number };

/** Percent rounded to an integer, or null when there is nothing to measure. */
export function percentOf(value: number, total: number): number | null {
  return total > 0 ? Math.round((value / total) * 100) : null;
}

/** Met or missed against a target; lower-is-better for durations. Gap is in points (or units for durations). */
export function versusTarget(actual: number | null, target: number, lowerIsBetter = false) {
  if (actual === null || !Number.isFinite(actual)) return { met: null as boolean | null, gap: null as number | null };
  const met = lowerIsBetter ? actual <= target : actual >= target;
  const gap = lowerIsBetter ? target - actual : actual - target;
  return { met, gap: Math.round(gap * 100) / 100 };
}

/** Semicircle gauge: arc endpoints for a fraction in [0, 1] (clamped), plus a target tick. */
export function gaugeGeometry(fraction: number, size: number, stroke = 12, target?: number) {
  const f = Number.isFinite(fraction) ? Math.min(1, Math.max(0, fraction)) : 0;
  const r = (size - stroke) / 2 - 4, cx = size / 2, cy = r + stroke / 2 + 4;
  const at = (q: number, radius = r) => [cx - radius * Math.cos(Math.PI * q), cy - radius * Math.sin(Math.PI * q)] as const;
  const arc = (a: number, b: number) => {
    const [x1, y1] = at(a), [x2, y2] = at(b);
    return `M${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 0 1 ${x2.toFixed(2)},${y2.toFixed(2)}`;
  };
  const tick = target === undefined || target >= 1 || target <= 0 ? null
    : { from: at(target, r - stroke / 2 - 4), to: at(target, r + stroke / 2 + 4) };
  return { fraction: f, track: arc(0, 1), fill: f > 0 ? arc(0, Math.max(f, 0.005)) : null, tick, cx, cy, height: cy + 2 };
}

/** Pie slices from 12 o'clock clockwise, in the order given. Zero parts are dropped. */
export function pieSlices(parts: { name: string; value: number }[], radius: number, cx = radius, cy = radius) {
  const kept = parts.filter(p => p.value > 0);
  const total = kept.reduce((sum, p) => sum + p.value, 0);
  let a = -Math.PI / 2;
  return kept.map(p => {
    const share = total ? p.value / total : 0;
    const a0 = a, a1 = a + share * Math.PI * 2; a = a1;
    const pt = (ang: number) => [cx + radius * Math.cos(ang), cy + radius * Math.sin(ang)] as const;
    const [x0, y0] = pt(a0), [x1, y1] = pt(a1);
    const path = share >= 0.9999
      ? `M${cx - radius},${cy} a${radius},${radius} 0 1 0 ${2 * radius},0 a${radius},${radius} 0 1 0 ${-2 * radius},0`
      : `M${cx},${cy} L${x0.toFixed(2)},${y0.toFixed(2)} A${radius},${radius} 0 ${a1 - a0 > Math.PI ? 1 : 0} 1 ${x1.toFixed(2)},${y1.toFixed(2)} Z`;
    return { ...p, share, percent: Math.round(share * 100), mid: (a0 + a1) / 2, path };
  });
}

/** Folds parts past the third into "Other" when there are more than four. */
export function foldParts<T extends { name: string; value: number }>(parts: T[], other = "Other") {
  const sorted = [...parts].filter(p => p.value > 0).sort((a, b) => b.value - a.value);
  if (sorted.length <= 4) return sorted.map(p => ({ name: p.name, value: p.value, folded: [] as string[] }));
  const rest = sorted.slice(3);
  return [...sorted.slice(0, 3).map(p => ({ name: p.name, value: p.value, folded: [] as string[] })),
    { name: other, value: rest.reduce((s, p) => s + p.value, 0), folded: rest.map(p => `${p.name} ${p.value}`) }];
}

/** A rounded axis top and evenly spaced ticks; never zero so empty data still draws an axis. */
export function axisTicks(values: (number | null)[], fixedMax?: number, count = 4) {
  const nums = values.filter((v): v is number => v !== null && Number.isFinite(v));
  const peak = Math.max(0, ...nums);
  if (fixedMax !== undefined) return { top: fixedMax, ticks: Array.from({ length: count + 1 }, (_, i) => Math.round((fixedMax * i) / count * 100) / 100) };
  // A 1/2/5 step keeps every tick on a round number (0, 20, 40 … rather than 17.5).
  const raw = Math.max(peak / count, 1), magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map(k => k * magnitude).find(k => k >= raw)!;
  const top = Math.max(step, Math.ceil(peak / step) * step);
  return { top, ticks: Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step) };
}

/** SVG path through points; null values break the line instead of dropping to zero. */
export function linePath(values: (number | null)[], x: (i: number) => number, y: (v: number) => number) {
  let out = "", open = false;
  values.forEach((v, i) => {
    if (v === null || !Number.isFinite(v)) { open = false; return; }
    out += `${open ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
    open = true;
  });
  return out;
}

/** End-of-line labels nudged apart so they never overlap (minimum gap in px). */
export function spreadLabels(ys: number[], gap = 16) {
  const order = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
  order.forEach((item, k) => { if (k && item.y - order[k - 1].y < gap) item.y = order[k - 1].y + gap; });
  const out = Array<number>(ys.length);
  order.forEach(item => { out[item.i] = item.y; });
  return out;
}

/** Cumulative scope and done counts as step events from ticket created/done times. */
export function burnupSteps(tickets: { created: number; done: number | null }[], start: number, end: number) {
  const points = new Set<number>([start]);
  tickets.forEach(t => { if (t.created >= start && t.created <= end) points.add(t.created); if (t.done !== null && t.done >= start && t.done <= end) points.add(t.done); });
  const steps = [...points].sort((a, b) => a - b).map(at => ({
    at,
    scope: tickets.filter(t => t.created <= at).length,
    done: tickets.filter(t => t.done !== null && t.done <= at).length,
  }));
  const last = steps[steps.length - 1];
  if (last.at < end) steps.push({ at: end, scope: last.scope, done: last.done });
  return steps;
}

/** Index of the day nearest to an x position on an evenly spaced axis. */
export function nearestIndex(x: number, left: number, width: number, count: number) {
  if (count <= 1 || width <= 0) return 0;
  return Math.max(0, Math.min(count - 1, Math.round(((x - left) / width) * (count - 1))));
}

/** Position in [0, 1] on a log scale between min and max (values are clamped). */
export function logPosition(value: number, min: number, max: number) {
  const v = Math.min(max, Math.max(min, value));
  return (Math.log(v) - Math.log(min)) / (Math.log(max) - Math.log(min));
}

/** Groups durations that round to the same 0.1 h, so a batch of tickets closed together becomes one counted bead. */
export function beadGroups(hours: number[]) {
  const groups = new Map<number, number>();
  hours.filter(h => Number.isFinite(h) && h >= 0).forEach(h => { const key = Math.round(h * 10) / 10; groups.set(key, (groups.get(key) || 0) + 1); });
  return [...groups].map(([value, count]) => ({ value, count })).sort((a, b) => a.value - b.value);
}

/** Median of finite numbers, or null for none. */
export function medianOf(values: number[]) {
  const s = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!s.length) return null;
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
