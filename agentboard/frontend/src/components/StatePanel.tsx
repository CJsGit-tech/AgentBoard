import { ReactNode } from "react";
import { useWorkspace } from "../app/WorkspaceContext";
export function StatePanel({
  children,
  empty,
  title = "Nothing here yet",
  action,
}: {
  children: ReactNode;
  empty?: boolean;
  title?: string;
  action?: ReactNode;
}) {
  const { preview, setPreview, mode, refresh } = useWorkspace();
  if (preview === "Loading")
    return (
      <section className="state-panel" role="status">
        <h2>Loading workspace…</h2>
        <div className="skeleton" />
        <div className="skeleton" />
      </section>
    );
  if (preview === "Error")
    return (
      <section className="state-panel" role="alert">
        <h2>Unable to load this view</h2>
        <p>
          Existing records are preserved. Unavailable data is not zero work.
        </p>
        <button onClick={() => mode === "connected" ? void refresh().catch(() => setPreview("Error")) : setPreview("Ready")}>Retry</button>
      </section>
    );
  if (empty || preview === "Empty")
    return (
      <section className="state-panel">
        <div className="empty-mark">＋</div>
        <h2>{title}</h2>
        <p>Create the first item or adjust your filters.</p>
        {action}
      </section>
    );
  return <>{children}</>;
}
