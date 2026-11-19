import { Ticket, statuses } from "../../api/types";
import { useState } from "react";
import { StatusBadge } from "../../components/StatusBadge";
import { TicketCard } from "./TicketCard";
export function TicketBoard({
  tickets,
  selected,
  onOpen,
}: {
  tickets: Ticket[];
  selected: string;
  onOpen: (id: string) => void;
}) {
  const [limits, setLimits] = useState<Record<string, number>>({});
  return (
    <div className="board">
      {statuses.map((s) => {
        const all = tickets.filter((t) => t.status === s);
        const limit = limits[s] || 4;
        return (
          <section className="board-lane" key={s}>
            <h2>
              <StatusBadge status={s} />
              <small>{all.length}</small>
            </h2>
            <div className="board-cards">
              {all.slice(0, limit).map((t) => (
                <TicketCard
                  key={t.id}
                  ticket={t}
                  selected={selected === t.id}
                  onOpen={() => onOpen(t.id)}
                />
              ))}
              {!all.length && <p className="lane-empty">No tickets</p>}
              {all.length > limit && (
                <button
                  onClick={() => setLimits({ ...limits, [s]: limit + 4 })}
                >
                  Load more · {all.length - limit} remaining
                </button>
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}
