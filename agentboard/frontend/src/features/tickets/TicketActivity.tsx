import { Ticket } from "../../api/types";
import { retained } from "../../api/mockAdapter";
import { useWorkspace } from "../../app/WorkspaceContext";
import { ActivityFeed } from "../activity/ActivityFeed";
export function TicketActivity({ ticket }: { ticket: Ticket }) {
  const { db } = useWorkspace();
  return (
    <section className="inspector-section">
      <details>
        <summary>Ticket activity</summary>
        <ActivityFeed
          events={retained(db.activity).filter((e) => e.ticketId === ticket.id)}
        />
      </details>
    </section>
  );
}
