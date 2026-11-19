import { Status, statuses } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { TagFilter } from "../../components/TagFilter";
export function TicketFilters({
  status,
  owner,
  sort,
  view,
  onStatus,
  onOwner,
  onSort,
  onView,
  count,
  featureTag,
  concernTag,
  featureTags,
  concernTags,
  onFeatureTag,
  onConcernTag,
}: {
  status: string;
  owner: string;
  sort: string;
  view: string;
  onStatus: (s: string) => void;
  onOwner: (s: string) => void;
  onSort: (s: string) => void;
  onView: (s: string) => void;
  count: number;
  featureTag: string[];
  concernTag: string[];
  featureTags: string[];
  concernTags: string[];
  onFeatureTag: (tags: string[]) => void;
  onConcernTag: (tags: string[]) => void;
}) {
  const { db, projectId } = useWorkspace();
  return (
    <div className="toolbar ticket-toolbar">
      <div className="segmented" role="group" aria-label="Ticket view">
        <button aria-pressed={view === "table"} onClick={() => onView("table")}>
          ▤ Table
        </button>
        <button aria-pressed={view === "board"} onClick={() => onView("board")}>
          ▥ Board
        </button>
      </div>
      <label htmlFor="ticketfilters-1">
        Status
        <select
          id="ticketfilters-1"
          aria-label="Filter tickets by status"
          value={status}
          onChange={(e) => onStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          {statuses.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </label>
      <label htmlFor="ticketfilters-2">
        Owner
        <select
          id="ticketfilters-2"
          aria-label="Filter tickets by owner"
          value={owner}
          onChange={(e) => onOwner(e.target.value)}
        >
          <option value="">All owners</option>
          <option value="unassigned">Unassigned</option>
          <option value="me">Me</option>
          {db.roles
            .filter((r) => r.projectId === projectId)
            .map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
        </select>
      </label>
      <label htmlFor="ticketfilters-3">
        Order
        <select
          id="ticketfilters-3"
          aria-label="Order tickets"
          value={sort}
          onChange={(e) => onSort(e.target.value)}
        >
          <option value="updated">Recently updated</option>
          <option value="priority">Priority · all sample records</option>
        </select>
      </label>
      <TagFilter title="Feature tags" tags={featureTags} selected={featureTag} onChange={onFeatureTag} />
      <TagFilter title="Concern tags" tags={concernTags} selected={concernTag} onChange={onConcernTag} />
      <small className="tag-filter-hint">Any tag within a group matches; feature and concern groups apply together.</small>
      <span className="result-count">{count} tickets</span>
    </div>
  );
}
