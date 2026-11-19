import { SaveFailureControl } from "../../components/SaveFailureControl";
import { useState } from "react";
import { Ticket, Priority, Status, statuses } from "../../api/types";
import { useWorkspace } from "../../app/WorkspaceContext";
export function TicketEditor({
  ticket,
  onSaved,
}: {
  ticket?: Ticket;
  onSaved: (id: string) => void;
}) {
  const { db, projectId, saveTicket, setDirty, mode } = useWorkspace();
  const [saving, setSaving] = useState(false);
  const [values, setValues] = useState({
    title: ticket?.title || "",
    description: ticket?.description || "",
    details: ticket?.details || "",
    ownerId: ticket?.ownerId || "",
    priority: ticket?.priority || ("Medium" as Priority),
    status: ticket?.status || ("Planned" as Status),
    blocker: ticket?.blocker || "",
    executionRole: ticket?.executionRole || "FE",
    workType: ticket?.workType || "BUILD",
    verification: ticket?.verification || (ticket?.workType === "BUG" ? "reported" : "not_applicable"),
    assignment: ticket?.assignment || "provisional",
    estimateDays: ticket?.estimateDays?.toString() || "",
    featureTags: ticket?.featureTags?.join(", ") || "",
    concernTags: ticket?.concernTags?.join(", ") || "",
  });
  const [error, setError] = useState("");
  const [errorField, setErrorField] = useState("");
  const change = (key: string, value: string) => {
    setError("");
    setErrorField("");
    setValues({ ...values, [key]: value });
    setDirty(true);
  };
  return (
    <form
      noValidate
      aria-label="ticket editor"
      className="ticket-editor"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!values.title.trim()) {
          setError("A ticket title is required.");
          setErrorField("title");
          e.currentTarget.querySelector<HTMLInputElement>("input")?.focus();
          return;
        }
        if (values.status === "Blocked" && !values.blocker.trim()) {
          setError("Explain the blocker before saving.");
          setErrorField("blocker");
          e.currentTarget
            .querySelector<HTMLTextAreaElement>(
              '[aria-label="Blocker explanation"]',
            )
            ?.focus();
          return;
        }
        if (values.estimateDays && (!Number.isFinite(Number(values.estimateDays)) || Number(values.estimateDays) <= 0)) {
          setError("Estimate must be a positive number of days.");
          setErrorField("estimate");
          e.currentTarget.querySelector<HTMLInputElement>("#ticketeditor-estimate")?.focus();
          return;
        }
        if (
          values.ownerId &&
          ![
            "me",
            ...db.roles
              .filter((r) => r.projectId === projectId)
              .map((r) => r.id),
          ].includes(values.ownerId)
        ) {
          setError("Choose an owner from this project.");
          setErrorField("owner");
          e.currentTarget.querySelector<HTMLSelectElement>("#ticketeditor-2")?.focus();
          return;
        }
        setSaving(true);
        const normalized = { ...values, title: values.title.trim(), estimateDays: values.estimateDays ? Number(values.estimateDays) : undefined,
          featureTags: splitTags(values.featureTags), concernTags: splitTags(values.concernTags), blocker: values.status === "Blocked" ? values.blocker.trim() : "" };
        try { const tid = await saveTicket(normalized, ticket); setError(""); onSaved(tid); }
        catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save ticket. Your draft is retained."); }
        finally { setSaving(false); }
      }}
    >
      <label htmlFor="ticketeditor-1">
        Title <span aria-hidden="true">*</span>
        <input
          id="ticketeditor-1"
          aria-label="Ticket title"
          required
          aria-invalid={!!error && !values.title.trim()}
          aria-describedby={errorField === "title" ? "ticketeditor-error" : undefined}
          value={values.title}
          onChange={(e) => change("title", e.target.value)}
        />
      </label>
      <div className="field-pair">
        <label htmlFor="ticketeditor-2">
          Owner
          <select
            id="ticketeditor-2"
            aria-label="Ticket owner"
            aria-invalid={errorField === "owner"}
            aria-describedby={errorField === "owner" ? "ticketeditor-error" : undefined}
            value={values.ownerId}
            onChange={(e) => change("ownerId", e.target.value)}
          >
            <option value="">Unassigned</option>
            <option value="me">Me</option>
            {db.roles
              .filter((r) => r.projectId === projectId)
              .map((r) => (
                <option value={r.id} key={r.id}>
                  {r.name}
                </option>
              ))}
          </select>
        </label>
        <label htmlFor="ticketeditor-3">
          Priority
          <select
            id="ticketeditor-3"
            aria-label="Ticket priority"
            value={values.priority}
            onChange={(e) => change("priority", e.target.value)}
          >
            {["High", "Medium", "Low"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
      </div>
      <label htmlFor="ticketeditor-4">
        Status
        <select
          id="ticketeditor-4"
          aria-label="Ticket status"
          value={values.status}
          onChange={(e) => change("status", e.target.value)}
        >
          {statuses.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </label>
      <label htmlFor="ticketeditor-5">
        Description
        <textarea
          id="ticketeditor-5"
          aria-label="Ticket description"
          rows={3}
          value={values.description}
          onChange={(e) => change("description", e.target.value)}
        />
      </label>
      {(values.status === "Blocked" || values.blocker) && (
        <label htmlFor="ticketeditor-6">
          Blocker explanation
          {values.status === "Blocked" && <span aria-hidden="true"> *</span>}
          <textarea
            id="ticketeditor-6"
            aria-label="Blocker explanation"
            rows={2}
            required={values.status === "Blocked"}
            aria-invalid={
              !!error && values.status === "Blocked" && !values.blocker.trim()
            }
            aria-describedby={errorField === "blocker" ? "ticketeditor-error" : undefined}
            value={values.blocker}
            onChange={(e) => change("blocker", e.target.value)}
          />
        </label>
      )}
      <div className="field-pair">
        <label htmlFor="ticketeditor-role">Execution role
          <select id="ticketeditor-role" value={values.executionRole} onChange={e => change("executionRole", e.target.value)}>
            <option value="FE">FE</option><option value="BE">BE</option>
          </select>
        </label>
        <label htmlFor="ticketeditor-type">Work type
          <select id="ticketeditor-type" value={values.workType} onChange={e => {
            const workType = e.target.value as "BUG" | "BUILD";
            setError("");
            setValues({ ...values, workType, verification: workType === "BUG" ? "reported" : "not_applicable" });
            setDirty(true);
          }}>
            <option value="BUILD">BUILD</option><option value="BUG">BUG</option>
          </select>
        </label>
      </div>
      <div className="field-pair">
        <label htmlFor="ticketeditor-verification">Verification
          <select id="ticketeditor-verification" value={values.verification} onChange={e => change("verification", e.target.value)}>
            {["reported", "investigating", "confirmed", "not_reproduced", "fixed", "not_a_bug", "not_applicable"].map(value => <option key={value}>{value}</option>)}
          </select>
        </label>
        <label htmlFor="ticketeditor-assignment">Assignment
          <select id="ticketeditor-assignment" value={values.assignment} onChange={e => change("assignment", e.target.value)}>
            <option value="confirmed">Confirmed</option><option value="provisional">Provisional</option>
          </select>
        </label>
      </div>
      <label htmlFor="ticketeditor-details">Details
        <textarea id="ticketeditor-details" aria-label="Ticket details" rows={4} value={values.details} onChange={e => change("details", e.target.value)} />
      </label>
      <label htmlFor="ticketeditor-estimate">Estimate (days)
        <input id="ticketeditor-estimate" aria-invalid={errorField === "estimate"} aria-describedby={errorField === "estimate" ? "ticketeditor-error" : undefined} type="number" min="0.1" step="0.1" value={values.estimateDays} onChange={e => change("estimateDays", e.target.value)} />
      </label>
      <label htmlFor="ticketeditor-feature-tags">Feature tags
        <input id="ticketeditor-feature-tags" placeholder="feature:task-coordination, ..." value={values.featureTags} onChange={e => change("featureTags", e.target.value)} />
      </label>
      <label htmlFor="ticketeditor-concern-tags">Concern tags
        <input id="ticketeditor-concern-tags" placeholder="concern:reliability, ..." value={values.concernTags} onChange={e => change("concernTags", e.target.value)} />
      </label>
      {error && (
        <p id="ticketeditor-error" role="alert" className="form-error">
          {error}
        </p>
      )}
      <SaveFailureControl />
      <div className="form-footer">
        <small>{mode === "mock" ? "Local preview changes" : "Saved to the connected workspace"}</small>
        <button className="primary" disabled={saving}>
          {ticket ? "Save ticket" : "Create ticket"}
        </button>
      </div>
    </form>
  );
}

function splitTags(input: string) {
  return [...new Set(input.split(",").map(tag => tag.trim()).filter(Boolean))];
}
