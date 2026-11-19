import { statuses, Ticket } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { StatusBadge } from "../../components/StatusBadge";
export function ProgressSummary({ tickets }: { tickets: Ticket[] }) {
  const { navigate } = useWorkspace();
  const done = tickets.filter((t) => t.status === "Done").length;
  return (
    <section className="panel progress-panel">
      <div className="section-heading">
        <div>
          <h2>Project totals</h2>
          <p>Task completion, not product completion</p>
        </div>
        <span className="completion">
          {done}
          <small> / {tickets.length} tickets done</small>
        </span>
      </div>
      <div
        className="progress-bar"
        aria-hidden="true"
      >
        {statuses.map((s) => (
          <div
            key={s}
            className={s.toLowerCase().replaceAll(" ", "-")}
            style={{ flex: tickets.filter((t) => t.status === s).length }}
          />
        ))}
      </div>
      <div className="status-counts">
        {statuses.map((s) => (
          <button
            key={s}
            onClick={() => navigate("/tickets?status=" + encodeURIComponent(s))}
          >
            <StatusBadge status={s} />
            <strong aria-label={`${tickets.filter((t) => t.status === s).length} ${s} tickets`}>
              {tickets.filter((t) => t.status === s).length}
            </strong>
          </button>
        ))}
      </div>
      <table className="sr-only">
        <caption>Ticket status counts</caption>
        <tbody>
          {statuses.map((s) => (
            <tr key={s}>
              <th scope="row">{s}</th>
              <td>{tickets.filter((t) => t.status === s).length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
