import { Activity, ticketDisplayReference } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
export interface Filters {
  ticket: string;
  agent: string;
  type: string;
  label: string;
  provenance: string;
  outcome: string;
  range: string;
}
export function ActivityFilters({
  filters: f,
  onChange,
  events,
}: {
  filters: Filters;
  onChange: (f: Filters) => void;
  events: Activity[];
}) {
  const { db, projectId } = useWorkspace();
  const distinct = (key: "agent" | "type" | "label" | "outcome") => [
    ...new Set(events.map((e) => e[key])),
  ];
  return (
    <div className="activity-filters">
      <label htmlFor="activityfilters-1">
        Ticket
        <select
          id="activityfilters-1"
          aria-label="Filter activity by ticket"
          value={f.ticket}
          onChange={(e) => onChange({ ...f, ticket: e.target.value })}
        >
          <option value="">All tickets</option>
          {db.tickets
            .filter((t) => t.projectId === projectId)
            .map((t) => (
              <option key={t.id} value={t.id}>
                {ticketDisplayReference(t) ? `${ticketDisplayReference(t)} · ` : ""}{t.title}
              </option>
            ))}
        </select>
      </label>
      {(["agent", "type", "label", "outcome"] as const).map((key) => (
        <label htmlFor={`activity-filter-${key}`} key={key}>
          {key[0].toUpperCase() + key.slice(1)}
          <select
            id={`activity-filter-${key}`}
            aria-label={"Filter activity by " + key}
            value={f[key]}
            onChange={(e) => onChange({ ...f, [key]: e.target.value })}
          >
            <option value="">All {key === "type" ? "types" : key + "s"}</option>
            {distinct(key).map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
      ))}
      <label htmlFor="activityfilters-3">
        Provenance
        <select
          id="activityfilters-3"
          aria-label="Filter activity by provenance"
          value={f.provenance}
          onChange={(e) => onChange({ ...f, provenance: e.target.value })}
        >
          <option value="">All sources</option>
          <option>Agent-reported</option>
          <option>Server-observed</option>
        </select>
      </label>
      <label htmlFor="activityfilters-4">
        Time range
        <select
          id="activityfilters-4"
          aria-label="Activity time range"
          value={f.range}
          onChange={(e) => onChange({ ...f, range: e.target.value })}
        >
          <option value="all">All retained activity</option>
          <option value="24">Last 24 hours</option>
          <option value="168">Last 7 days</option>
          <option value="720">Last 30 days</option>
          <option value="1">Last hour</option>
        </select>
      </label>
    </div>
  );
}
