import { Ticket } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
export function BlockerList({ tickets }: { tickets: Ticket[] }) {
  const { db, navigate } = useWorkspace();
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>Needs your attention</h2>
        <span>{tickets.length} blocked</span>
      </div>
      {tickets.length ? (
        tickets.map((t) => (
          <button
            key={t.id}
            className="blocker-row"
            onClick={() => navigate("/tickets/" + t.id)}
          >
            <span className="blocker-dot" aria-hidden="true">△</span>
            <span>
              <strong>{t.title}</strong>
              <small>{t.blocker?.trim() || "No blocker explanation provided."}</small>
            </span>
            <span>
              {db.roles.find((r) => r.id === t.ownerId)?.name ||
                (t.ownerId === "me" ? "Me" : "Unassigned")}
            </span>
          </button>
        ))
      ) : (
        <p className="muted">No blocked tickets in this project.</p>
      )}
    </section>
  );
}
