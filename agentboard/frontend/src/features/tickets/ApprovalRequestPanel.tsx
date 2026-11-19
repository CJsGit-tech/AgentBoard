import { useState } from "react";
import { Approval, Ticket } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
import { ShieldAlert } from "lucide-react";
export function ApprovalRequestPanel({ ticket }: { ticket: Ticket }) {
  const { db, mode } = useWorkspace();
  const [variant, setVariant] = useState<Approval["state"]>("Pending");
  const requests = db.approvals.filter((a) => a.ticketId === ticket.id);
  if (!requests.length)
    return (
      <section className="inspector-section">
        <h3>Agent requests</h3>
        <p className="muted small">
          No protected change requests for this ticket.
        </p>
      </section>
    );
  return (
    <section className="inspector-section">
      <div className="section-heading">
        <h3>Proposed agent changes</h3>
        <ShieldAlert size={15} />
      </div>
      {mode === "mock" && <label htmlFor="approvalrequestpanel-1" className="preview-control">
        Request state demonstration
        <select
          id="approvalrequestpanel-1"
          aria-label="Approval request state"
          value={variant}
          onChange={(e) => setVariant(e.target.value as typeof variant)}
        >
          {["Pending", "Unsupported", "Stale", "Expired", "Rejected"].map(
            (x) => (
              <option key={x}>{x}</option>
            ),
          )}
        </select>
      </label>}
      {requests.map((a) => (
        <article className="request-card" key={a.id}>
          <div className="request-meta">
            <span>
              {a.client} · {mode === "mock" ? variant : a.state}
            </span>
              <span>{mode === "mock" ? variant : a.state}</span>
          </div>
          <h4>{a.action}</h4>
          <div className="diff removed">− {a.before}</div>
          <div className="diff added">+ {a.after}</div>
          <p className="notice">
            {(mode === "mock" ? variant : a.state) === "Pending"
              ? `Continue in ${a.client} to review this request. Current data stays unchanged.`
              : (mode === "mock" ? variant : a.state) === "Unsupported"
                ? "Client approval is unavailable. The protected change is not applied; the pending badge remains for retry."
                : (mode === "mock" ? variant : a.state) === "Stale"
                  ? "The target changed. This request cannot be applied; obtain fresh client approval."
                  : (mode === "mock" ? variant : a.state) === "Expired"
                    ? "This request expired. No change was applied."
                    : "Request rejected. No business change was applied."}
          </p>
        </article>
      ))}
      <small className="muted">
        {mode === "mock" ? "Preview states do not approve or execute changes. Multiple pending requests are shown independently." : "These requests are read-only here. Review or decide them in the requesting client."}
      </small>
    </section>
  );
}
