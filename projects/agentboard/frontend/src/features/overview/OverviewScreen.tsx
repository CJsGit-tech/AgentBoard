import { ArrowUpRight } from "lucide-react";
import { useWorkspace } from "../../app/WorkspaceContext";
import { PageHeader } from "../../components/PageHeader";
import { StatePanel } from "../../components/StatePanel";
import { ProgressSummary } from "./ProgressSummary";
import { BlockerList } from "./BlockerList";
import { ApprovalBadge } from "../../components/ApprovalBadge";
import { ActivityFeed } from "../activity/ActivityFeed";
import { retained } from "../../api/mockAdapter";
export function OverviewScreen() {
  const { db, projectId, navigate } = useWorkspace();
  const p = db.projects.find((x) => x.id === projectId);
  const tickets = db.tickets.filter((t) => t.projectId === projectId);
  const pending = db.approvals.filter(
    (a) =>
      tickets.some((t) => t.id === a.ticketId) &&
      ["Pending", "Unsupported"].includes(a.state),
  );
  return (
    <>
      <PageHeader
        title={p?.name || "Project overview"}
        description={p?.purpose || "Project progress and recent work."}
        actions={
          <button onClick={() => navigate("/tickets")}>
            Open tickets
            <ArrowUpRight size={16} />
          </button>
        }
      />
      <StatePanel
      >
        {!tickets.length ? (
          <section className="state-panel">
            <div className="empty-mark">＋</div>
            <h2>No tickets yet</h2>
            <p>This project has no tickets, so task completion is not available yet.</p>
            <button className="primary" onClick={() => navigate("/tickets?create=1")}>
              Create first ticket
            </button>
          </section>
        ) : <>
        <ProgressSummary tickets={tickets} />
        <div className="overview-columns">
          <BlockerList
            tickets={tickets.filter((t) => t.status === "Blocked")}
          />
          <section className="panel">
            <div className="section-heading">
              <h2>Client approvals</h2>
              <ApprovalBadge count={pending.length} />
            </div>
            <p className="muted">
              {pending.length} pending request{pending.length !== 1 ? "s" : ""}.
              Review protected agent changes in Codex or Claude.
            </p>
            {pending.map((a) => (
              <button
                className="approval-row"
                key={a.id}
                onClick={() => navigate("/tickets/" + a.ticketId)}
              >
                <strong>
                  {db.tickets.find((t) => t.id === a.ticketId)?.title}
                </strong>
                <small>
                  {a.client} · {a.action}
                </small>
              </button>
            ))}
            {!pending.length && <p>No pending requests.</p>}
          </section>
        </div>
        <section className="panel">
          <div className="section-heading">
            <h2>Recent activity</h2>
            <button onClick={() => navigate("/activity")}>
              View activity →
            </button>
          </div>
          <ActivityFeed
            events={retained(db.activity)
              .filter((a) => a.projectId === projectId)
              .slice(0, 4)}
          />
        </section>
        </>}
      </StatePanel>
    </>
  );
}
