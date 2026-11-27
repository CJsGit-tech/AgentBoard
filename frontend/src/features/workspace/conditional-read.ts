export type Snapshot<T> = { path: string; etag: string | null; data: T };

/** A validator is useful only with the exact representation it validates. */
export async function conditionalRead<T>(path: string, previous?: Snapshot<T>): Promise<Snapshot<T>> {
  const cached = previous?.path === path ? previous : undefined;
  const response = await fetch("/api/" + path, {
    cache: "no-store",
    signal: AbortSignal.timeout(30000),
    headers: { "X-AgentBoard-UI": "1", ...(cached?.etag ? { "If-None-Match": cached.etag } : {}) },
  });
  if (response.status === 304 && cached?.etag) return cached;
  if (!response.ok) {
    const text = await response.text();
    let message = text;
    try { message = JSON.parse(text).detail || text; } catch { /* Non-JSON gateway response. */ }
    throw Object.assign(new Error(message || response.statusText), { status: response.status });
  }
  return { path, etag: response.headers.get("ETag"), data: await response.json() as T };
}
