import { Ticket, ticketDisplayReference } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { ApprovalBadge } from "../../components/ApprovalBadge";
import { formatTime } from "../../api/mockAdapter";
export function TicketCard({
  ticket: t,
  selected,
  onOpen,
}: {
  ticket: Ticket;
  selected: boolean;
  onOpen: () => void;
}) {
  const { db } = useWorkspace();
  const pending = db.approvals.filter(
    (a) => a.ticketId === t.id && ["Pending", "Unsupported"].includes(a.state),
  ).length;
  return (
    <article className={"ticket-card " + (selected ? "chosen" : "")}>
      {ticketDisplayReference(t) && <small className="mono">{ticketDisplayReference(t)}</small>}
      <a
        href={"#/tickets/" + t.id}
        onClick={(e) => {
          e.preventDefault();
          onOpen();
        }}
      >
        {t.title}
      </a>
      {pending > 0 && <ApprovalBadge count={pending} />}
      <div className="card-meta">
        <span>
          {db.roles.find((r) => r.id === t.ownerId)?.name ||
            (t.ownerId === "me" ? "Me" : "Unassigned")}
        </span>
        <span>{t.priority}</span>
      </div>
      <div className="card-meta"><span>{t.executionRole || "—"} · {t.workType || "—"}</span><span>{t.estimateDays ? t.estimateDays + " days" : "Estimate unknown"}</span></div>
      {(t.featureTags?.length || t.concernTags?.length) ? <small>{[...(t.featureTags || []), ...(t.concernTags || [])].join(" · ")}</small> : null}
      <small>Updated {formatTime(t.updated)}</small>
    </article>
  );
}
