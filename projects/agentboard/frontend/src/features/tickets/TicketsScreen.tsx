import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { useWorkspace } from "../../app/WorkspaceContext";
import { PageHeader } from "../../components/PageHeader";
import { StatePanel } from "../../components/StatePanel";
import { TicketFilters } from "./TicketFilters";
import { TicketTable } from "./TicketTable";
import { TicketBoard } from "./TicketBoard";
import { TicketInspector } from "./TicketInspector";
export function TicketsScreen({ route }: { route: string }) {
  const { db, projectId, dirty, setDirty, navigate } = useWorkspace();
  const saved = JSON.parse(
    sessionStorage.getItem("agentboard-ticket-filters-" + projectId) || "{}",
  );
  const [status, setStatus] = useState(saved.status || "");
  const [owner, setOwner] = useState(saved.owner || "");
  const [featureTag, setFeatureTag] = useState<string[]>([]);
  const [concernTag, setConcernTag] = useState<string[]>([]);
  const [sort, setSort] = useState(saved.sort || "updated");
  const [view, setView] = useState(
    localStorage.getItem("agentboard-ticket-view") || "table",
  );
  const [selected, setSelected] = useState("");
  useEffect(() => {
    const [path, query] = route.split("?");
    const params = new URLSearchParams(query);
    if (params.has("status")) setStatus(params.get("status") || "");
    if (params.has("owner")) setOwner(params.get("owner") || "");
    if (params.has("create")) setSelected("new");
    else if (path.split("/")[2]) setSelected(path.split("/")[2]);
  }, [route]);
  useEffect(() => {
    sessionStorage.setItem(
      "agentboard-ticket-filters-" + projectId,
      JSON.stringify({ status, owner, sort }),
    );
  }, [projectId, status, owner, sort]);
  const tickets = db.tickets
    .filter(
      (t) =>
        t.projectId === projectId &&
        (!status || t.status === status) &&
        (!owner || (owner === "unassigned" ? !t.ownerId : t.ownerId === owner)) &&
        (!featureTag.length || featureTag.some((tag) => t.featureTags?.includes(tag))) &&
        (!concernTag.length || concernTag.some((tag) => t.concernTags?.includes(tag))),
    )
    .sort((a, b) =>
      sort === "priority"
        ? ["High", "Medium", "Low"].indexOf(a.priority) -
          ["High", "Medium", "Low"].indexOf(b.priority)
        : Date.parse(b.updated) - Date.parse(a.updated),
    );
  const ticket = db.tickets.find(
    (t) => t.id === selected && t.projectId === projectId,
  );
  const projectTickets = db.tickets.filter((item) => item.projectId === projectId);
  const featureTags = [...new Set(projectTickets.flatMap((item) => item.featureTags || []))].sort();
  const concernTags = [...new Set(projectTickets.flatMap((item) => item.concernTags || []))].sort();
  const open = (id: string) => {
    if (dirty && !confirm("Discard unsaved ticket changes?")) return;
    setDirty(false);
    setSelected(id);
  };
  const close = () => {
    if (dirty && !confirm("Discard unsaved ticket changes?")) return;
    setDirty(false);
    setSelected("");
    if (route.split("?")[0] !== "/tickets") navigate("/tickets");
  };
  return (
    <>
      <PageHeader
        title="Tickets"
        description="Keep the work clear. Keep the context close."
        actions={
          <button className="primary" onClick={() => open("new")}>
            <Plus size={16} />
            New ticket
          </button>
        }
      />
      <div className={"tickets-layout " + (selected ? "has-inspector" : "")}>
        <section className="ticket-surface">
          <TicketFilters
            status={status}
            owner={owner}
            sort={sort}
            view={view}
            count={tickets.length}
            onStatus={setStatus}
            onOwner={setOwner}
            onSort={setSort}
            onView={(v) => {
              setView(v);
              localStorage.setItem("agentboard-ticket-view", v);
            }}
            featureTag={featureTag}
            concernTag={concernTag}
            featureTags={featureTags}
            concernTags={concernTags}
            onFeatureTag={setFeatureTag}
            onConcernTag={setConcernTag}
          />
          <StatePanel
            empty={!tickets.length}
            title="No matching tickets"
            action={<button onClick={() => open("new")}>Create ticket</button>}
          >
            {view === "table" ? (
              <TicketTable
                tickets={tickets}
                selected={selected}
                onOpen={open}
              />
            ) : (
              <TicketBoard
                tickets={tickets}
                selected={selected}
                onOpen={open}
              />
            )}
          </StatePanel>
        </section>
        {selected && (selected === "new" || ticket) ? (
          <TicketInspector
            ticket={ticket}
            onClose={close}
            onSaved={(id) => setSelected(id)}
          />
        ) : selected ? (
          <section className="state-panel">
            <h2>Ticket unavailable</h2>
            <p>This ticket is missing or belongs to another project.</p>
            <button onClick={close}>Back to tickets</button>
          </section>
        ) : null}
      </div>
    </>
  );
}
