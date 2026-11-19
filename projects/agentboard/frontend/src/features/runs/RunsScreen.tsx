import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { useWorkspace } from "../../app/WorkspaceContext";
import { Approval, Provider, Run, RunSettings, decideApproval, getRun, getRunSettings, listApprovals, listRuns, setRunSettings, startRun } from "./sdkApi";
import { ApiError } from "../../api/restClient";
import "./runs.css";

const terminal = (status: Run["status"]) => status === "completed" || status === "failed";
const readable = (value: unknown) => typeof value === "string" ? value : JSON.stringify(value, null, 2);

export function RunsScreen() {
  const { mode, projectId, db } = useWorkspace();
  const [provider, setProvider] = useState<Provider>("codex");
  const [prompt, setPrompt] = useState("");
  const [contextSelection, setContextSelection] = useState("");
  const [runs, setRuns] = useState<Run[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [settings, setSettings] = useState<RunSettings | null>(null);
  const [settingsBusy, setSettingsBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyApproval, setBusyApproval] = useState("");
  const submittingRef = useRef(false);
  const runRequestKey = useRef<{ key: string; projectId: string; provider: Provider; prompt: string; context: string } | null>(null);
  const project = db.projects.find((item) => item.id === projectId);
  const projectTickets = db.tickets.filter((item) => item.projectId === projectId);
  const projectDocuments = db.documents.filter((item) => item.projectId === projectId);
  const selectedContext = contextSelection ? { kind: contextSelection.startsWith("ticket:") ? "ticket" as const : "document" as const, id: contextSelection.slice(contextSelection.indexOf(":") + 1) } : undefined;

  const refresh = useCallback(async () => {
    if (mode !== "connected" || !projectId) return;
    const [runResult, approvalResult] = await Promise.all([listRuns(projectId), listApprovals(projectId)]);
    setRuns(runResult.items);
    setApprovals(approvalResult.items);
  }, [mode, projectId]);

  useEffect(() => {
    if (mode !== "connected") return;
    let active = true;
    const load = async () => {
      try {
        const settingsResult = await getRunSettings();
        if (active) { setSettings(settingsResult); setError(""); }
        if (!projectId) return;
        const [runResult, approvalResult] = await Promise.all([listRuns(projectId), listApprovals(projectId)]);
        if (active) { setRuns(runResult.items); setApprovals(approvalResult.items); }
      } catch (cause) { if (active) setError(cause instanceof Error ? cause.message : "Could not load runs."); }
    };
    void load();
    const timer = window.setInterval(() => { void load(); }, 4000);
    return () => { active = false; window.clearInterval(timer); };
  }, [mode, projectId]);

  const toggleRuns = async () => {
    if (!settings) return;
    setSettingsBusy(true); setError("");
    try { setSettings(await setRunSettings(!settings.enabled)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not update workspace settings."); }
    finally { setSettingsBusy(false); }
  };

  useEffect(() => {
    if (mode !== "connected" || !projectId) return;
    const activeRuns = runs.filter((run) => !terminal(run.status));
    if (!activeRuns.length) return;
    let active = true;
    const timer = window.setInterval(async () => {
      const fresh = await Promise.all(activeRuns.map((run) => getRun(projectId, run.id).catch(() => null)));
      if (!active) return;
      setRuns((current) => {
        const updates = new Map(fresh.filter((run): run is Run => run !== null).map((run) => [run.id, run]));
        return current.map((run) => updates.get(run.id) || run);
      });
    }, 2500);
    return () => { active = false; window.clearInterval(timer); };
  }, [mode, projectId, runs]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const normalizedPrompt = prompt.trim();
    if (!projectId || !normalizedPrompt || submittingRef.current) return;
    const previousRequest = runRequestKey.current;
    const sameRequest = previousRequest?.projectId === projectId && previousRequest.provider === provider && previousRequest.prompt === normalizedPrompt && previousRequest.context === contextSelection;
    const idempotencyKey = sameRequest ? previousRequest.key : crypto.randomUUID();
    runRequestKey.current = { key: idempotencyKey, projectId, provider, prompt: normalizedPrompt, context: contextSelection };
    submittingRef.current = true;
    setLoading(true); setError(""); setNotice("");
    try {
      const run = await startRun(projectId, provider, normalizedPrompt, idempotencyKey, selectedContext);
      setRuns((current) => [run, ...current.filter((item) => item.id !== run.id)]);
      runRequestKey.current = null;
      setPrompt("");
    } catch (cause) {
      if (cause instanceof ApiError && (cause.code === "sdk_runs_disabled" || cause.code === "provider_disabled")) {
        setError(cause.message);
        if (cause.code === "provider_disabled") void getRunSettings().then(setSettings).catch(() => undefined);
      } else setError(cause instanceof Error ? cause.message : "Could not start the run.");
    } finally { setLoading(false); submittingRef.current = false; }
  };

  const decide = async (approval: Approval, decision: "approve" | "reject") => {
    setBusyApproval(approval.id); setError(""); setNotice("");
    try {
      const result = await decideApproval(projectId, approval, decision);
      setApprovals((current) => current.map((item) => item.id === approval.id ? { ...item, status: result.status } : item));
      setNotice(decision === "approve" ? "Proposed change approved and applied." : "Proposed change declined.");
      await refresh();
    } catch (cause) {
      setError(cause instanceof ApiError && cause.code === "approval_mismatch"
        ? "The proposed change or record revision changed. Reload the approval before deciding."
        : cause instanceof ApiError && cause.code === "stale_revision"
          ? "The record has changed since this proposal. No decision was applied."
          : cause instanceof Error ? cause.message : "Could not record the decision.");
      await refresh().catch(() => undefined);
    } finally { setBusyApproval(""); }
  };

  return <section className="runs-screen">
    <header className="page-header"><div><p className="eyebrow">WORKSPACE EXECUTION</p><h1>Agent runs</h1><p>Choose a configured provider, review progress, and decide on proposed record changes.</p></div></header>
    {mode !== "connected" ? <section className="run-callout" role="status"><strong>Connect to a workspace to use SDK runs.</strong><p>Run mode is available only with an authenticated server session. Preview mode never makes live calls.</p></section> : <>
      <section className="run-panel"><div className="run-section-title"><div><h2>Workspace SDK runs</h2><p>Enable or disable SDK execution for everyone in this workspace.</p></div><label className="run-toggle"><input type="checkbox" checked={settings?.enabled ?? false} disabled={!settings || settingsBusy} onChange={() => void toggleRuns()} /><span>{settingsBusy ? "Saving…" : settings?.enabled ? "Enabled" : "Disabled"}</span></label></div>
        {!settings && <p role="status">Loading workspace settings…</p>}
        <p className="run-ready-state">{settings?.ready ? "At least one provider is ready." : "No configured provider is ready."} {settings && Object.entries(settings.providers).filter(([, value]) => !value.available).map(([name, value]) => `${name}: ${value.reason}`).join(" · ")}</p>
      </section>
      {!projectId ? <section className="state-panel"><h2>Select a project</h2><p>Workspace settings are available above. Select a project before starting or reviewing runs.</p></section> : <>
      <section className="run-panel"><div className="run-section-title"><div><h2>Start a run</h2><p>Runs begin only when you submit this form.</p></div><span className="run-ready-state">{settings?.providers[provider].available ? "Provider ready" : settings?.providers[provider].reason || "Checking provider…"}</span></div>
        <form onSubmit={submit} className="run-form">
          <label>Project<input value={project?.name || projectId} readOnly /></label>
          <label>Provider<select value={provider} onChange={(event) => setProvider(event.target.value as Provider)}><option value="codex" disabled={!settings?.providers.codex.available}>Codex SDK</option><option value="claude" disabled={!settings?.providers.claude.available}>Claude Agent SDK</option></select></label>
          <label>Record context (optional)<select value={contextSelection} onChange={(event) => setContextSelection(event.target.value)}><option value="">No record selected</option><optgroup label="Tickets">{projectTickets.map((item) => <option key={item.id} value={`ticket:${item.id}`}>{item.title}</option>)}</optgroup><optgroup label="Documents">{projectDocuments.map((item) => <option key={item.id} value={`document:${item.id}`}>{item.title}</option>)}</optgroup></select></label>
          <label className="run-prompt-label">Prompt<textarea required minLength={1} maxLength={20000} rows={5} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Describe the work for the selected agent…" /></label>
          <div className="run-form-footer"><span>Server configuration limits which providers are available.</span><button className="primary" disabled={loading || !prompt.trim() || !settings?.enabled || !settings.providers[provider].available}>{loading ? "Starting…" : "Start run"}</button></div>
        </form>
      </section>
      {error && <p role="alert" className="run-error">{error}</p>}{notice && <p role="status" className="run-notice">{notice}</p>}
      <section className="run-section"><div className="run-section-title"><div><h2>Runs</h2><p>Progress refreshes automatically while a run is active.</p></div><button className="secondary" onClick={() => void refresh().catch((cause) => setError(cause.message))}>Refresh</button></div>
        {runs.length ? <div className="run-list">{runs.map((run) => <article className="run-card" key={run.id}><div className="run-card-heading"><div><h3>{run.provider === "codex" ? "Codex" : "Claude Agent"} <small>· {new Date(run.created_at).toLocaleString()}</small></h3></div><span className={`run-status status-${run.status}`}>{run.status}</span></div>
          {!!run.activity.length && <ol className="run-activity">{run.activity.map((item, index) => <li key={`${item.at}-${index}`}><time>{new Date(item.at).toLocaleTimeString()}</time><span>{item.text}</span></li>)}</ol>}
          {run.status === "failed" && <div className="run-failure" role="alert"><strong>Run failed</strong><p>{run.error || "The provider could not complete this run."}</p></div>}
          {run.result && <details className="run-result"><summary>Run result</summary><pre>{run.result}</pre></details>}
          {approvals.filter((approval) => approval.run_id === run.id).map((approval) => <ApprovalPanel key={approval.id} approval={approval} busy={busyApproval === approval.id} onDecision={(decision) => void decide(approval, decision)} />)}
        </article>)}</div> : <section className="state-panel"><h2>No runs yet</h2><p>Start a run when the selected provider is ready for this workspace.</p></section>}
      </section>
      </>}
    </>}
  </section>;
}

function ApprovalPanel({ approval, busy, onDecision }: { approval: Approval; busy: boolean; onDecision: (decision: "approve" | "reject") => void }) {
  const [acknowledged, setAcknowledged] = useState(false);
  const pending = approval.status === "pending";
  return <section className="run-approval" aria-labelledby={`approval-${approval.id}`}><div className="approval-heading"><div><p className="eyebrow">HUMAN REVIEW REQUIRED</p><h4 id={`approval-${approval.id}`}>Proposed {approval.operation === "delete" ? "Delete" : "Update"} · {approval.target_kind}</h4></div><span className={`run-status status-${approval.status}`}>{approval.status}</span></div>
    <dl className="approval-meta"><div><dt>Target</dt><dd>{approval.target_label}</dd></div><div><dt>Base revision</dt><dd>{approval.base_revision}</dd></div></dl>
    <h5>{approval.operation === "delete" ? "Deletion consequence" : "Exact proposed change"}</h5><pre className="approval-change">{readable(approval.change_preview)}</pre>
    {pending && <><label className="approval-ack"><input type="checkbox" checked={acknowledged} onChange={(event) => setAcknowledged(event.target.checked)} /> I reviewed this exact {approval.operation === "delete" ? "deletion" : "change"} and its base revision.</label><div className="approval-actions"><button className="primary" disabled={!acknowledged || busy} onClick={() => onDecision("approve")}>{busy ? "Saving…" : approval.operation === "delete" ? "Approve deletion" : "Approve update"}</button><button className="secondary" disabled={busy} onClick={() => onDecision("reject")}>Decline</button></div></>}
  </section>;
}
