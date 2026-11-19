import { useEffect, useRef, useState } from "react";
import { Activity } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { PageHeader } from "../../components/PageHeader";
import { StatePanel } from "../../components/StatePanel";
import { id, timestamp, retained } from "../../api/mockAdapter";
import { ActivityFeed } from "./ActivityFeed";
import { ActivityFilters, Filters } from "./ActivityFilters";
import { LiveActivityControls } from "./LiveActivityControls";
export function ActivityScreen() {
  const { db, projectId, preview, setPreview, commit, mode, liveConnected, liveResync, clearLiveResync } = useWorkspace();
  const [filters, setFilters] = useState<Filters>({
    ticket: "",
    agent: "",
    type: "",
    label: "",
    provenance: "",
    outcome: "",
    range: mode === "connected" ? "all" : "24",
  });
  const [mockConnected, setMockConnected] = useState(true);
  const [buffer, setBuffer] = useState<Activity[]>([]);
  const [gap, setGap] = useState(false);
  const [message, setMessage] = useState("");
  const last = useRef<Activity | null>(null);
  const scrolled = useRef(false);
  const projectActivity = mode === "mock" ? retained(db.activity) : db.activity;
  const all = projectActivity.filter((e) => e.projectId === projectId);
  useEffect(() => {
    const listener = () => {
      scrolled.current = window.scrollY > 100;
    };
    window.addEventListener("scroll", listener);
    return () => window.removeEventListener("scroll", listener);
  }, []);
  useEffect(() => {
    setFilters({
      ticket: "",
      agent: "",
      type: "",
      label: "",
      provenance: "",
      outcome: "",
      range: mode === "connected" ? "all" : "24",
    });
    setBuffer([]);
    setGap(false);
  }, [projectId]);
  const isConnected = mode === "connected" ? liveConnected : mockConnected && preview !== "Disconnected";
  const record = (event: Activity) => {
    commit(
      (db) =>
        db.activity.some((e) => e.id === event.id)
          ? db
          : { ...db, activity: [event, ...db.activity] },
      "",
    );
  };
  const incoming = () => {
    const event: Activity = {
      id: id("reported"),
      projectId,
      ticketId: db.tickets.find((t) => t.projectId === projectId)?.id,
      agent: "Claude",
      action: "Reported a tool call for ticket context",
      type: "Tool call",
      label: "mcp",
      outcome: "Succeeded",
      provenance: "Agent-reported",
      time: timestamp(),
    };
    last.current = event;
    if (!isConnected || scrolled.current) {
      setBuffer((old) => [...old, event]);
      setMessage("New activity is buffered so your place stays stable.");
    } else {
      record(event);
      setMessage("Incoming sample event added automatically.");
    }
  };
  const events = all.filter(
    (e) =>
      (!filters.ticket || e.ticketId === filters.ticket) &&
      (!filters.agent || e.agent === filters.agent) &&
      (!filters.type || e.type === filters.type) &&
      (!filters.label || e.label === filters.label) &&
      (!filters.provenance || e.provenance === filters.provenance) &&
      (!filters.outcome || e.outcome === filters.outcome) &&
      (filters.range === "all" || Date.now() - Date.parse(e.time) < Number(filters.range) * 3600000),
  );
  return (
    <>
      <PageHeader
        title="Activity"
        description="Who worked on what, and when. Review the evidence."
      />
      {mode === "mock" ? <LiveActivityControls
        connected={isConnected}
        buffered={buffer.length}
        gap={gap}
        onToggle={() => {
          if (!isConnected) {
            setGap(true);
            buffer.forEach(record);
            setBuffer([]);
            setPreview("Ready");
            setMockConnected(true);
          } else setMockConnected(false);
        }}
        onSimulate={incoming}
        onReplay={() => {
          if (last.current) {
            record(last.current);
            setMessage(
              "Duplicate event key ignored; no second entry was added.",
            );
          } else setMessage("Simulate an event first, then replay it.");
        }}
        onFlush={() => {
          buffer.forEach(record);
          setBuffer([]);
          setMessage("Buffered events shown.");
        }}
        onCleanup={() => {
          commit((db) => ({ ...db, activity: retained(db.activity) }), "");
          setMessage(
            "Expired activity removed. Tickets, documents and revisions preserved.",
          );
        }}
      /> : <div className={"live-controls"}>
        <div className={"live-state " + (!liveConnected ? "stale" : "")}><strong>{liveConnected ? "Connected to live activity" : "Reconnecting to activity stream…"}</strong><small>New server events refresh workspace records and approvals.</small></div>
        {liveResync && <p className="notice" role="status">The retained activity cursor expired during disconnection. Workspace data has been resynchronized. <button type="button" className="text-button" onClick={clearLiveResync}>Dismiss</button></p>}
      </div>}
      <div className="context-note">
        {mode === "connected" ? "Activity retention uses server receive time. Time range filters use when the event occurred." : "Rolling 30-day retention. Expired events are excluded immediately, before cleanup."} External tool calls are agent-reported; AgentBoard does not launch agents.
      </div>
      <ActivityFilters filters={filters} onChange={setFilters} events={all} />
      <div className="section-heading activity-count">
        <span>{events.length} retained events</span>
        <small>
          Project: {db.projects.find((p) => p.id === projectId)?.name}
        </small>
      </div>
      <p className="sr-only" role="status" aria-live="polite">
        {message}
      </p>
      {message && <p className="inline-feedback">{message}</p>}
      <StatePanel>
        <section className="panel activity-panel">
          <ActivityFeed events={events}
            onAgentFilter={(agent) => setFilters((current) => ({ ...current, agent }))}
            onLabelFilter={(label) => setFilters((current) => ({ ...current, label }))}
          />
        </section>
      </StatePanel>
    </>
  );
}
