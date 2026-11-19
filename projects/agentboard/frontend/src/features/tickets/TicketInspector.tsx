import { useEffect } from "react";
import { X } from "lucide-react";
import { Ticket, ticketDisplayReference } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { StatusBadge } from "../../components/StatusBadge";
import { ApprovalBadge } from "../../components/ApprovalBadge";
import { TicketEditor } from "./TicketEditor";
import { TicketDocumentLinks } from "./TicketDocumentLinks";
import { ApprovalRequestPanel } from "./ApprovalRequestPanel";
import { TicketActivity } from "./TicketActivity";
export function TicketInspector({
  ticket,
  onClose,
  onSaved,
}: {
  ticket?: Ticket;
  onClose: () => void;
  onSaved: (id: string) => void;
}) {
  const { db } = useWorkspace();
  const count = db.approvals.filter(
    (a) =>
      a.ticketId === ticket?.id && ["Pending", "Unsupported"].includes(a.state),
  ).length;
  useEffect(() => {
    const listener = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, [onClose]);
  return (
    <aside className="ticket-inspector" aria-label="Ticket details">
      <div className="inspector-top">
        <small>TICKET DETAILS{ticket ? ticketDisplayReference(ticket) ? ` · ${ticketDisplayReference(ticket)}` : "" : " · NEW"}</small>
        <button
          aria-label="Close ticket details"
          className="iconbutton"
          onClick={onClose}
        >
          <X size={19} />
        </button>
      </div>
      <h2>{ticket?.title || "New ticket"}</h2>
      {ticket && (
        <div className="badges">
          <StatusBadge status={ticket.status} />
          {count > 0 && <ApprovalBadge count={count} />}
        </div>
      )}
      <TicketEditor
        key={ticket?.id || "new"}
        ticket={ticket}
        onSaved={onSaved}
      />
      {ticket && (
        <>
          <TicketDocumentLinks ticket={ticket} />
          <ApprovalRequestPanel ticket={ticket} />
          <TicketActivity ticket={ticket} />
        </>
      )}
    </aside>
  );
}
