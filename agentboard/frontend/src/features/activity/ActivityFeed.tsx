import { Activity } from "../../api/types";
import { formatTime } from "../../api/mockAdapter";
import { useWorkspace } from "../../app/WorkspaceContext";
import { ArrowUpRight, ArrowRight } from "lucide-react";
export function ActivityFeed({ events, onAgentFilter, onLabelFilter }: {
  events: Activity[];
  onAgentFilter?: (agent: string) => void;
  onLabelFilter?: (label: string) => void;
}) {
  const { db, navigate } = useWorkspace();
  if (!events.length)
    return (
      <div className="activity-empty">
        <p>No retained activity is available within the 30-day window.</p>
        <small>
          External reporting may be incomplete; absence is not proof of no work.
        </small>
      </div>
    );
  return (
    <ol className="activity-feed">
      {events.map((e) => (
        <li key={e.id}>
          <span
            className={
              "event-icon " +
              (e.provenance === "Agent-reported" ? "reported" : "observed")
            }
          >
            {e.provenance === "Agent-reported" ? "↗" : "✓"}
          </span>
          <div>
            <div className="event-heading">
              {onAgentFilter ? <button type="button" className="text-button event-filter" aria-label={`Show activity from ${e.agent}`} onClick={() => onAgentFilter(e.agent)}>{e.agent}</button> : <strong>{e.agent}</strong>}
              <span>{e.action}</span>
              <span
                className={
                  "event-outcome " +
                  (e.outcome === "Succeeded" ? "success" : "")
                }
              >
                {e.outcome}
              </span>
            </div>
            {e.ticketId && (
              <a
                className="event-ticket"
                href={"#/tickets/" + e.ticketId}
                onClick={(event) => {
                  event.preventDefault();
                  navigate("/tickets/" + e.ticketId);
                }}
              >
                {db.tickets.find((t) => t.id === e.ticketId)?.title ||
                  "Ticket unavailable"}
                <ArrowUpRight size={12} />
              </a>
            )}
            {e.before !== undefined && (
              <div className="event-change">
                <span>{e.before}</span>
                <ArrowRight size={12} />
                <strong>{e.after}</strong>
              </div>
            )}
            <div className="event-meta">
              <time dateTime={e.time}>{formatTime(e.time)}</time>
              <span>{e.provenance}</span>
              {onLabelFilter ? <button type="button" className="label-chip event-filter" aria-label={`Show activity labeled ${e.label}`} onClick={() => onLabelFilter(e.label)}>{e.label}</button> : <span className="label-chip">{e.label}</span>}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
