import { Ticket, ticketDisplayReference } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { StatusBadge } from "../../components/StatusBadge";
import { ApprovalBadge } from "../../components/ApprovalBadge";
import { formatTime } from "../../api/mockAdapter";
export function TicketTable({
  tickets,
  selected,
  onOpen,
}: {
  tickets: Ticket[];
  selected: string;
  onOpen: (id: string) => void;
}) {
  const { db } = useWorkspace();
  return (
    <div
      className="table-wrap"
      tabIndex={0}
      role="region"
      aria-label="Tickets table scroll region"
    >
      <table>
        <caption className="sr-only">Project tickets</caption>
        <thead>
          <tr>
            <th scope="col">Ticket</th>
            <th scope="col">Status</th>
            <th scope="col">Owner</th>
            <th scope="col">Priority</th>
            <th scope="col">Approval</th>
            <th scope="col">Updated</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => {
            const pending = db.approvals.filter(
              (a) =>
                a.ticketId === t.id &&
                ["Pending", "Unsupported"].includes(a.state),
            ).length;
            return (
              <tr key={t.id} className={t.id === selected ? "selected" : ""}>
                <th scope="row">
                  <a
                    href={"#/tickets/" + t.id}
                    onClick={(e) => {
                      e.preventDefault();
                      onOpen(t.id);
                    }}
                  >
                    {t.title}
                  </a>
                  {ticketDisplayReference(t) && <small className="mono">{ticketDisplayReference(t)}</small>}
                </th>
                <td>
                  <StatusBadge status={t.status} />
                </td>
                <td>
                  {db.roles.find((r) => r.id === t.ownerId)?.name ||
                    (t.ownerId === "me" ? "Me" : "Unassigned")}
                </td>
                <td>
                  <span className={"priority " + t.priority.toLowerCase()}>
                    {t.priority === "High"
                      ? "↑"
                      : t.priority === "Low"
                        ? "↓"
                        : "−"}{" "}
                    {t.priority}
                  </span>
                </td>
                <td>
                  {pending ? (
                    <ApprovalBadge count={pending} />
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>
                  <time title={new Date(t.updated).toISOString()}>
                    {formatTime(t.updated)}
                  </time>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
