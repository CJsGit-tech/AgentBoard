import { sdkRequest } from "../../api/restClient";

export type Provider = "codex" | "claude";
export type Run = { id: string; project_id: string; provider: Provider; status: "queued" | "running" | "completed" | "failed"; activity: { type: string; text: string; at: string }[]; result: string | null; error: string | null; created_at: string; updated_at: string };
export type Approval = { id: string; run_id: string; target_kind: string; target_id: string; target_label: string; operation: "update" | "delete"; base_revision: number; changes: Record<string, unknown>; change_preview: Record<string, unknown>; change_hash: string; status: string; created_at: string };
export type RunSettings = { enabled: boolean; ready: boolean; providers: Record<Provider, { available: boolean; reason: string | null }> };
const path = (projectId: string) => `/api/v1/projects/${encodeURIComponent(projectId)}`;
const json = (body: unknown, extra?: Record<string, string>): RequestInit => ({ method: "POST", headers: extra, body: JSON.stringify(body) });
export const listRuns = (projectId: string) => sdkRequest<{ items: Run[] }>(`${path(projectId)}/runs`);
export const getRun = (projectId: string, runId: string) => sdkRequest<Run>(`${path(projectId)}/runs/${encodeURIComponent(runId)}`);
export const startRun = (projectId: string, provider: Provider, prompt: string, idempotencyKey: string, context?: { kind: "ticket" | "document"; id: string }) => sdkRequest<Run>(`${path(projectId)}/runs`, json({ provider, prompt, context_kind: context?.kind, context_id: context?.id }, { "Idempotency-Key": idempotencyKey }));
export const listApprovals = (projectId: string) => sdkRequest<{ items: Approval[] }>(`${path(projectId)}/approvals`);
export const decideApproval = (projectId: string, approval: Approval, decision: "approve" | "reject") => sdkRequest<{ id: string; status: string }>(
  `${path(projectId)}/approvals/${encodeURIComponent(approval.id)}/decision`,
  json({ decision, change_hash: approval.change_hash, expected_revision: approval.base_revision }, { "Idempotency-Key": crypto.randomUUID() }),
);
export const getRunSettings = () => sdkRequest<RunSettings>("/api/v1/settings/sdk-runs");
export const setRunSettings = (enabled: boolean) => sdkRequest<RunSettings>("/api/v1/settings/sdk-runs", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled }) });
