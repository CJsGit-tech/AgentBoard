import { useSyncExternalStore } from "react";
import { blocks, conflicts, inFlight, operations, type OperationStore } from "./operation-store";
import "./operations.css";

export function useOperations(store = operations) { return useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot); }
export function useOperationLock(resources: string[]) { return useOperations().some(op => blocks(op) && conflicts(op.resources, resources)); }
export function OperationFeedback({ store = operations }: { store?: OperationStore }) {
  const items = useOperations(store);
  return <section className="operation-feedback" aria-label="Pending changes" aria-live="polite" aria-relevant="additions text">
    {items.map(op => <div key={op.id} className="operation-notice" data-phase={op.phase} data-pending={inFlight(op)}>
      <span className="operation-mark" aria-hidden="true">{inFlight(op) ? "◌" : "!"}</span>
      <span><strong>{op.label}</strong><span role={op.phase === "failed" || op.phase === "sync-failed" || op.phase === "uncertain" ? "alert" : "status"}>{op.message}</span></span>
      {!inFlight(op) && (blocks(op)
        ? <button type="button" onClick={() => void store.retry(op.id)}>{op.phase === "uncertain" ? "Check saved state" : "Retry sync"}</button>
        : <button type="button" aria-label="Dismiss operation error" onClick={() => store.dismiss(op.id)}>Dismiss</button>)}
    </div>)}
  </section>;
}
