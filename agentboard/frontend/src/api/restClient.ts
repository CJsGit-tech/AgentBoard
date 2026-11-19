import { Activity, Database, Doc, Project, Revision, Role, Ticket } from "./types";

const base = ((import.meta as any).env?.VITE_AGENTBOARD_API_BASE || "").replace(/\/$/, "");
let csrfToken = "";
export class ApiError extends Error {
  status: number; code?: string;
  constructor(status: number, message: string, code?: string) { super(message); this.status = status; this.code = code; }
}
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && csrfToken) headers.set("X-CSRF-Token", csrfToken);
  const response = await fetch(base + path, { ...init, method, headers, credentials: "include" });
  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, body?.error?.message || `Request failed (${response.status})`, body?.error?.code);
  return body as T;
}
// SDK run UI shares the local CSRF handling used by the workspace API.
export function sdkRequest<T>(path: string, init: RequestInit = {}): Promise<T> { return request<T>(path, init); }
const json = (method: string, body: unknown, key = false): RequestInit => ({ method, headers: key ? { "Idempotency-Key": crypto.randomUUID() } : undefined, body: JSON.stringify(body) });
export async function restoreSession() { const result = await request<{ csrf_token: string }>("/api/v1/session"); csrfToken = result.csrf_token; }
async function items<T>(path: string): Promise<T[]> {
  const result: T[] = [];
  let cursor: string | undefined;
  do {
    const query = new URLSearchParams({ limit: "100" });
    if (cursor) query.set("cursor", cursor);
    const page = await request<{ items: T[]; next_cursor?: string }>(`${path}${path.includes("?") ? "&" : "?"}${query}`);
    result.push(...page.items);
    cursor = page.next_cursor;
  } while (cursor);
  return result;
}
const projectPath = (p: string) => "/api/v1/projects/" + encodeURIComponent(p);
export const documentKinds = [
  "api-example-index", "architecture-index", "architecture-topic", "contract-index", "design-index",
  "design-topic", "document", "document-index", "example-index", "mcp-contract-index",
  "metadata-catalog", "product-vision", "schema-index", "screen-approval", "screen-inventory",
  "ticket", "ticket-index", "user-story", "user-story-index",
];
const statusToWire: Record<Ticket["status"], string> = { Planned:"planned", "In progress":"in_progress", Blocked:"blocked", Done:"done" };
const wireToStatus: Record<string, Ticket["status"]> = { planned:"Planned", in_progress:"In progress", blocked:"Blocked", done:"Done" };
const approvalStatus: Record<string, Database["approvals"][number]["state"]> = {
  pending: "Pending", unsupported: "Unsupported", rejected: "Rejected", expired: "Expired", stale: "Stale",
};
const outcomeLabel: Record<string, string> = {
  success: "Succeeded", succeeded: "Succeeded", failed: "Failed", started: "Started",
  pending: "Pending", rejected: "Rejected", cancelled: "Cancelled",
};
const allTags = (x: {featureTags?:string[]; concernTags?:string[]}) => [...(x.featureTags || []), ...(x.concernTags || [])];
function mapProject(p:any): Project { return { id:p.id, name:p.name, purpose:p.purpose || "", updated:p.updated_at, revision:p.revision || 1 }; }
function mapRole(r:any): Role { return { id:r.id, projectId:r.project_id, name:r.name, responsibilities:r.responsibilities, revision:r.revision || 1 }; }
function mapTicket(t:any): Ticket {
 const tags = Array.isArray(t.tags) ? t.tags : [];
 const displayReference = typeof t.source_id === "string" && /^T-\d{3}$/.test(t.source_id) ? t.source_id : undefined;
 return { id:t.id, displayReference, projectId:t.project_id, title:t.title, description:t.description || "", details:t.details || "", status:wireToStatus[t.status] || "Planned", priority:t.priority === "normal" ? "Medium" : (t.priority || "low").replace(/^./,(s:string)=>s.toUpperCase()),
 ownerId:t.owner_kind === "role" ? t.role_id : t.owner_kind === "builder" ? "me" : "", blocker:t.blocker_reason || "", links:[], updated:t.updated_at, revision:t.revision || 1,
 featureTags:tags.filter((x:string)=>x.startsWith("feature:")), concernTags:tags.filter((x:string)=>x.startsWith("concern:")), executionRole:t.execution_role, workType:t.work_type, estimateDays:t.estimate_days, estimateScope:t.estimate_scope, estimateBasis:t.estimate_basis, verification:t.verification, assignment:t.assignment };
}
function mapRevision(v:any): Revision { return { id:v.id, number:v.version, content:v.content, updated:v.created_at, author:v.source === "builder" ? "Builder" : v.source }; }
export async function loadDatabase(selectedProjectId?: string): Promise<Database> {
 const projectRows = await items<any>("/api/v1/projects"); const projects = projectRows.map(mapProject);
  const roles:Role[]=[]; const tickets:Ticket[]=[]; const documents:Doc[]=[]; const activity:Activity[]=[]; const approvals:Database["approvals"]=[];
 const selectedProject = projects.find(p => p.id === selectedProjectId) || projects[0];
 for (const project of (selectedProject ? [selectedProject] : [])) {
  const prefix=projectPath(project.id);
  const [rr,tr,dr,er]=await Promise.all([items<any>(prefix+"/roles"),items<any>(prefix+"/tickets"),items<any>(prefix+"/documents"),items<any>(prefix+"/activity")]);
  roles.push(...rr.map(mapRole)); tickets.push(...tr.map(mapTicket));
  const linksByTicket = await Promise.all(tr.map(async t => [t.id, await items<any>(prefix+`/tickets/${t.id}/documents`)] as const));
  for (const [id,links] of linksByTicket) { const t=tickets.find(x=>x.id===id); if(t) t.links=links.map((l:any)=>({documentId:l.document_id,relation:l.relationship === "output" ? "Output" : "Context"})); }
  const requestsByTicket = await Promise.all(tr.map(async t => [t.id, await items<any>(prefix+`/tickets/${t.id}/mutation-requests`)] as const));
  for (const [ticketId,requests] of requestsByTicket) approvals.push(...requests.map((request:any)=>({
    id:request.id, ticketId, action:request.operation, before:`Revision ${request.base_revision}`,
    after:Object.keys(request.proposed_changes||{}).length?JSON.stringify(request.proposed_changes,null,2):"No pending changes",
    client:request.requester_client_id, state:approvalStatus[request.status] || "Expired",
  })));
  for (const d of dr) {
   const versions=(await items<any>(prefix+`/documents/${d.id}/versions`)).sort((a,b)=>b.version-a.version);
   documents.push({id:d.id,projectId:d.project_id,title:d.title,description:d.description,kind:d.kind, revision:d.revision || 1,
    featureTags:(d.tags||[]).filter((x:string)=>x.startsWith("feature:")), concernTags:(d.tags||[]).filter((x:string)=>x.startsWith("concern:")),
    sourceFilename:d.source === "upload" ? d.source_id : undefined,
    originalFrontmatter:d.source === "upload" ? d.original_frontmatter : undefined,
    uploadedAt:d.source === "upload" ? d.created_at : undefined,
    revisions:versions.length?versions.map(mapRevision):[{id:d.current_version_id,number:d.version||1,content:d.content||"",updated:d.updated_at,author:"Builder"}]});
  }
  activity.push(...er.map((e:any)=>({id:e.id,projectId:e.project_id,ticketId:e.ticket_id,agent:e.agent_name,action:e.action,type:(e.event_type||"").replaceAll("_"," ").replace(/^./,(x:string)=>x.toUpperCase()),label:(e.labels||[]).join(", "),outcome:outcomeLabel[(e.outcome||"").toLowerCase()] || (e.outcome||""),provenance:e.provenance === "agent_reported" ? "Agent-reported" as const : "Server-observed" as const,time:e.occurred_at,before:e.before,after:e.after})));
 }
 return {projects,roles,tickets,documents,activity,approvals};
}
export async function createProject(body:{name:string;purpose:string}) { return mapProject(await request<any>("/api/v1/projects",json("POST",body,true))); }
export async function updateProject(p:Project, changes:{name:string;purpose:string}) { return mapProject(await request<any>(projectPath(p.id),json("PATCH",{expected_revision:p.revision||1,changes}))); }
export async function deleteProject(p:Project) { return request<void>(projectPath(p.id),json("DELETE",{expected_revision:p.revision||1,confirm:true})); }
export async function createRole(projectId:string, body:{name:string;responsibilities:string}) { return mapRole(await request<any>(projectPath(projectId)+"/roles",json("POST",body,true))); }
export async function updateRole(projectId:string,r:Role,changes:{name:string;responsibilities:string}) { return mapRole(await request<any>(projectPath(projectId)+`/roles/${r.id}`,json("PATCH",{expected_revision:r.revision||1,changes}))); }
function priorityToWire(priority:string) { return priority.toLowerCase()==="medium"?"normal":priority.toLowerCase(); }
function ticketMetadata(v:any) { const workType=v.workType || "BUILD"; return { execution_role:v.executionRole || "FE", work_type:workType, estimate_days:v.estimateDays ? Number(v.estimateDays) : 1, estimate_scope:v.estimateScope || "build", estimate_basis:v.estimateBasis || "User estimate", tags:allTags(v), verification:v.verification || (workType === "BUG" ? "reported" : "not_applicable"), assignment:v.assignment || "provisional" }; }
function ticketChanges(v:any) { return { title:v.title.trim(), description:v.description||"", priority:priorityToWire(v.priority||"Medium"), status:statusToWire[v.status as Ticket["status"]]||"planned", owner_kind:v.ownerId==="me"?"builder":v.ownerId?"role":"unassigned", role_id:v.ownerId && v.ownerId!=="me"?v.ownerId:null, blocker_reason:v.status==="Blocked"?(v.blocker||null):null, details:v.details||"", ...ticketMetadata(v) }; }
export async function createTicket(projectId:string,v:any) {
 return mapTicket(await request<any>(projectPath(projectId)+"/tickets",json("POST",ticketChanges(v),true)));
}
export async function updateTicket(projectId:string,t:Ticket,v:any) { return mapTicket(await request<any>(projectPath(projectId)+`/tickets/${t.id}`,json("PATCH",{expected_revision:t.revision||1,changes:ticketChanges(v)}))); }
export function documentPayload(v:any, source:"manual"|"upload"="manual", sourceId?:string) {
 const payload={title:v.title.trim(),content:v.content,description:v.description||"",kind:normalizeKind(v.kind),tags:allTags(v),source,source_id:sourceId||null} as Record<string, unknown>;
 if (source === "upload" && typeof v.originalFrontmatter === "string" && v.originalFrontmatter.length) payload.original_frontmatter=v.originalFrontmatter;
 return payload;
}
export function normalizeKind(kind:string) { const normalized=kind.toLowerCase(); return documentKinds.includes(normalized)?normalized:"document"; }
export async function createDocument(projectId:string,v:any,source:"manual"|"upload"="manual",sourceId?:string) { return request<any>(projectPath(projectId)+"/documents",json("POST",documentPayload(v,source,sourceId),true)); }
export async function updateDocument(projectId:string,d:Doc,v:any) { const {title,content,description,kind,tags}=documentPayload(v); return request<any>(projectPath(projectId)+`/documents/${d.id}`,json("PATCH",{expected_revision:d.revision||1,changes:{title,content,description,kind,tags}})); }
export async function restoreDocument(projectId:string,d:Doc,r:Revision) { return request<any>(projectPath(projectId)+`/documents/${d.id}/versions/restore`,json("POST",{expected_revision:d.revision||1,version_id:r.id})); }
export async function linkDocument(projectId:string,t:Ticket,documentId:string,relation:"Context"|"Output") { return request<any>(projectPath(projectId)+`/tickets/${t.id}/documents`,json("POST",{document_id:documentId,relationship:relation.toLowerCase()},true)); }
export async function unlinkDocument(projectId:string,t:Ticket,documentId:string,relation:"Context"|"Output") { return request<void>(projectPath(projectId)+`/tickets/${t.id}/documents/${documentId}/${relation.toLowerCase()}?expected_revision=${t.revision||1}`,{method:"DELETE"}); }
export async function projectTags(projectId:string) { return (await request<{items:string[]}>(projectPath(projectId)+"/tags")).items; }
