export type Phase = "writing" | "syncing" | "sync-failed" | "uncertain" | "failed";
export type Operation = Readonly<{ id: number; resources: readonly string[]; label: string; completed: string; phase: Phase; message: string }>;
export type Mutation<T> = {
  resources: string[]; label: string; completed: string;
  write: () => Promise<T>;
  sync: (value: T) => Promise<void>;
  /** Read-only reconciliation. Throw if the saved outcome cannot be established. */
  reconcile?: () => Promise<T>;
  confirmed?: (value: T) => void;
  settled?: (value: T) => void;
};
export type Result<T> = { state: "confirmed"; value: T } | { state: "blocked" | "uncertain" | "sync-failed" };
export const projectResource = (id: string) => "project:" + id;
export const blocks = (op: Operation) => op.phase !== "failed";
export const inFlight = (op: Operation) => op.phase === "writing" || op.phase === "syncing";
export function conflicts(first: readonly string[], second: readonly string[]) {
  return first.some(key => second.includes(key));
}
export function isUncertain(error: unknown) {
  const status = (error as { status?: number })?.status;
  return status === undefined || status === 408 || status >= 500;
}

/** Application lifetime ownership: leaving a component never releases a write lock. */
export class OperationStore {
  private sequence = 0;
  private snapshot: readonly Operation[] = [];
  private listeners = new Set<() => void>();
  private retries = new Map<number, () => Promise<void>>();
  // Invalidates workspace reads begun before a new write or its confirmed response.
  epoch = 0;
  getSnapshot = () => this.snapshot;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  locked(resources: readonly string[]) { return this.snapshot.some(op => blocks(op) && conflicts(op.resources, resources)); }
  get pending() { return this.snapshot.some(blocks); }
  private emit() { for (const listener of this.listeners) listener(); }
  private change(id: number, patch: Partial<Operation>) { this.snapshot = this.snapshot.map(op => op.id === id ? { ...op, ...patch } : op); this.emit(); }
  dismiss(id: number) {
    const op = this.snapshot.find(item => item.id === id);
    if (!op || blocks(op)) return;
    this.remove(id);
  }
  private remove(id: number) { this.retries.delete(id); this.snapshot = this.snapshot.filter(op => op.id !== id); this.emit(); }
  async retry(id: number) { await this.retries.get(id)?.(); }

  async run<T>(config: Mutation<T>): Promise<Result<T>> {
    if (this.locked(config.resources)) return { state: "blocked" };
    const id = ++this.sequence;
    this.epoch++;
    // Replace only old non-blocking errors in the same context.
    this.snapshot = [...this.snapshot.filter(op => blocks(op) || !conflicts(op.resources, config.resources)),
      { id, resources: [...config.resources], label: config.label, completed: config.completed, phase: "writing", message: config.label + "…" }];
    this.emit();
    let value: T;
    let confirmed = false;
    const sync = async () => {
      const op = this.snapshot.find(item => item.id === id);
      if (!op || op.phase === "syncing") return;
      this.change(id, { phase: "syncing", message: confirmed ? "Syncing changes…" : "Checking saved state…" });
      try {
        if (!confirmed) {
          if (!config.reconcile) throw new Error("Check the latest saved state before retrying this action.");
          value = await config.reconcile();
          confirmed = true;
          this.epoch++;
          config.confirmed?.(value);
        }
        await config.sync(value);
        this.remove(id);
        try { config.settled?.(value); } catch { /* Saved data remains confirmed if view focus is unavailable. */ }
      } catch {
        this.change(id, { phase: confirmed ? "sync-failed" : "uncertain", message: confirmed
          ? config.completed + "; refresh failed. Retry sync to load the latest data."
          : "The response was interrupted. The action may have completed. Check saved state before trying again." });
      }
    };
    this.retries.set(id, sync);
    try {
      value = await config.write();
      confirmed = true;
      this.epoch++;
    } catch (error) {
      if (isUncertain(error)) {
        this.change(id, { phase: "uncertain", message: "The response was interrupted. The action may have completed. Check saved state before trying again." });
        // First repair is always a read, never a replay of write().
        await sync();
        return this.snapshot.some(op => op.id === id) ? { state: confirmed ? "sync-failed" : "uncertain" } : { state: "confirmed", value: value! };
      }
      this.retries.delete(id);
      this.change(id, { phase: "failed", message: config.label + " failed. " + (error instanceof Error ? error.message : "Review the error and try again.") });
      throw error;
    }
    try { config.confirmed?.(value); }
    catch { /* A view callback must not turn a confirmed write into a rejected one. */ }
    await sync();
    return this.snapshot.some(op => op.id === id) ? { state: "sync-failed" } : { state: "confirmed", value };
  }
}
export const operations = new OperationStore();
