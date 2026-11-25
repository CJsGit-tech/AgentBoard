export const kinds = [
  "projects",
  "tickets",
  "milestones",
  "runs",
  "roles",
  "documents",
] as const;
export type Kind = (typeof kinds)[number];
export type Page = Kind | "activity" | "dashboard" | "canvas" | "assistant";
export type TicketView = "" | "attention" | "overdue";
export type Row = {
  id: string;
  revision: number;
  name: string;
  project?: string;
  description?: string;
  checkout_path?: string;
  milestone?: string;
  status?: string;
  role?: string;
  due?: string;
  documents?: string[];
  output_documents?: string[];
  source_documents?: string[];
  mode?: "Edit" | "Read only";
  document_type?: string;
  canvas_versions?: { screen_count?: number | null; version: number; digest: string; asset_key: string; published_at: string; publisher: string | null; change_note: string | null; sources: { document_id: string; name: string; revision: number }[] }[];
  previews?: { filename: string; digest: string }[];
  tags?: string[];
  work_type?: string;
  execution_role?: string;
  created_at?: string;
  updated_at?: string;
  latest_edit_role?: string | null;
  latest_editor?: string | null;
  instructions?: string;
  content?: string;
  ticket?: string;
  agent?: string;
  assistant_run_id?: string;
  note?: string;
  updated?: string;
};
export type Change = {
  id: string;
  project: string;
  actor: string;
  editor_role?: string | null;
  time: string;
  action: string;
  kind: Kind;
  record: string;
  name: string;
  changes: [string, unknown, unknown][];
};
export type Workspace = Record<Kind, Row[]> & {
  reviews: ChangeReview[];
  activity: Change[];
  trash: { k: Kind; r: Row }[];
};
export type WorkspaceRefresh = (verify?: (data: Workspace) => boolean) => Promise<void>;
export type Editor = { kind: Kind; row?: Row; project?: string; panel?: "Links" | "History" };
export const names: Record<Page, string> = {
  projects: "Projects",
  dashboard: "Dashboard",
  canvas: "Canvas",
  tickets: "Tickets",
  milestones: "Milestones",
  runs: "Agent runs",
  roles: "Roles",
  documents: "Documents",
  activity: "Activity",
  assistant: "InApp Assistant",
};

export type AssistantRunStatus =
  | "Queued"
  | "Running"
  | "Waiting for input"
  | "Blocked"
  | "Completed"
  | "Failed"
  | "Cancelled";
export type AssistantRun = {
  request_id?: string;
  cancelled?: boolean;
  id: string;
  name?: string;
  project: string;
  conversation_id: string;
  board_run_id: string | null;
  ticket_id: string | null;
  model: string;
  mode: "Read only" | "Edit";
  role_name?: string | null;
  role_id?: string | null;
  status: AssistantRunStatus;
  last_confirmed_step?: string | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
  restore_point?: { created_at?: string; expires_at?: string; [key: string]: unknown } | null;
  checks?: Array<string | Record<string, unknown>>;
  changed_files?: string[];
};
export type AssistantConfig = {
  provider: string;
  models: { id: string; name: string }[];
  credential: { configured: boolean; source: "environment" | "session" | "none" };
  notice: string;
};
export type AssistantExecution = {
  status: "Not configured" | "Restart required" | "Ready" | "Unavailable";
  host_folder: string;
  container_folder: "/workspaces";
  project_path: string;
  access: "read/write";
  message: string;
  setup_command: string;
};
export type AssistantConversationSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};
export type AssistantMessage = {
  id: string;
  role: string;
  content: string;
  run_id: string | null;
  created_at: string;
};
export type AssistantConversation = AssistantConversationSummary & {
  project: string;
  messages: AssistantMessage[];
  runs: AssistantRun[];
};
export type AssistantRunEvent = {
  seq: number;
  type: string;
  payload: Record<string, unknown>;
  created_at: string;
};
export type AssistantRunEvents = { events: AssistantRunEvent[]; run: AssistantRun };
export type AssistantRestorePreview = {
  conflicts: string[];
  changes: string[];
  [key: string]: unknown;
};
export type ReviewDocument = {
  id: string; kind: Kind; name: string; revision: number; fingerprint: string;
  fields: Record<string, unknown>; baseline?: ReviewDocument | null;
};
export type ReviewFinding = { document_id: string; outcome: "No update needed" | "Update required"; reason: string };
export type ChangeReview = {
  id: string; project: string; subject: string; revision: number; review_type: string;
  operation: "Edit" | "Delete"; request: string; status: string; conclusion: string | null;
  rationale: string; findings: ReviewFinding[]; reviewer: string | null;
  confirmed_by: string | null; confirmation_note: string | null;
  created_at: string; updated_at: string; superseded: boolean;
  snapshot: { subject: ReviewDocument; documents: ReviewDocument[]; missing_context: boolean };
};
export const currentReview = (db: Workspace, id: string) => db.reviews?.find(review => review.subject === id && !review.superseded);
export const reviewReady = (review?: ChangeReview) => !!review && ["Ready", "Confirmed"].includes(review.status) && review.operation === "Edit";
export const single: Record<Kind, string> = {
  projects: "project",
  tickets: "ticket",
  milestones: "milestone",
  runs: "run report",
  roles: "role",
  documents: "document",
};
export const documentGroups = [
  { label: "Product", types: [
    { value: "product-vision", label: "Product Vision" },
    { value: "user-story", label: "User Story" },
  ] },
  { label: "Architecture", types: [
    { value: "architecture-topic", label: "Architecture Topic" },
  ] },
  { label: "Design", types: [
    { value: "design-topic", label: "Design Topic" },
    { value: "screen-inventory", label: "Screen Inventory" },
  ] },
  { label: "Review", types: [
    { value: "review-report", label: "Review Report" },
    { value: "review-evidence", label: "Review Evidence" },
  ] },
  { label: "Unclassified", types: [
    { value: "unclassified", label: "Unclassified" },
  ] },
];
export const documentTypes = documentGroups.flatMap((group) => group.types);
export const workTypes = [
  { value: "BUILD", label: "BUILD" },
  { value: "BUG", label: "BUG" },
  { value: "UNCLASSIFIED", label: "Unclassified" },
];
export const latestEditor = (row: Row) =>
  row.latest_edit_role || row.latest_editor || "—";
export const linkedDocument = (ticket: Row, id: string) =>
  ticket.documents?.includes(id) || ticket.output_documents?.includes(id);

export const statuses = ["Planned", "In progress", "Blocked", "Done"];
export const runStates = [
  "Queued",
  "Running",
  "Waiting for input",
  "Blocked",
  "Completed",
  "Failed",
  "Cancelled",
];
export const tone = (s: string) => s.startsWith("Due ") ? "#80520f" :
  ({
    "In progress": "#5148a4",
    Running: "#5148a4",
    Queued: "#64748b",
    Done: "#346552",
    Completed: "#346552",
    Blocked: "#80520f",
    "Waiting for input": "#80520f",
    "Awaiting confirmation": "#80520f",
    "Needs updates": "#80520f",
    Failed: "#a33935",
    Overdue: "#a33935",
    Planned: "#64748b",
    Cancelled: "#64748b",
    "Not configured": "#64748b",
    "Restart required": "#80520f",
    Ready: "#346552",
    Unavailable: "#a33935",
    Confirmed: "#346552",
    Declined: "#64748b",
  })[s] || "#64748b";
export function localDate(offset = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, "0"),
    String(d.getDate()).padStart(2, "0"),
  ].join("-");
}
export const shortDate = (s?: string) =>
  s
    ? new Date(s + "T12:00:00").toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      })
    : "—";
export const stamp = (s?: string) =>
  s
    ? new Date(s).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";
export const done = (rows: Row[]) =>
  rows.filter((r) => r.status === "Done").length;
export const percent = (rows: Row[]) =>
  rows.length ? Math.round((100 * done(rows)) / rows.length) : 0;
export const nameOf = (db: Workspace, k: Kind, id?: string) =>
  db[k].find((v) => v.id === id)?.name || "—";
export const scoped = (rows: Row[], scope: string, kind: Kind) =>
  rows.filter(
    (r) => !scope || (kind === "projects" ? r.id : r.project) === scope,
  );
export const dueSoon = (r: Row) =>
  r.status !== "Done" && !!r.due && r.due <= localDate(3);
export const isOverdue = (r: Row) =>
  r.status !== "Done" && !!r.due && r.due < localDate();
export const attentionStates = ["Blocked", "Waiting for input", "Failed"];
export function newestRuns(runs: Row[]) {
  return [...runs].sort((a,b) => (b.updated || "").localeCompare(a.updated || ""));
}
export function attentionReasons(tickets: Row[], runs: Row[]) {
  const latest = new Map<string, Row>();
  for (const run of newestRuns(runs)) {
    if (run.ticket && !latest.has(run.ticket)) latest.set(run.ticket, run);
  }
  const reasons = new Map<string, string>();
  for (const ticket of tickets) {
    if (ticket.status === "Done") continue;
    const reason = ticket.status === "Blocked" ? "Blocked" : latest.get(ticket.id)?.status;
    if (reason && attentionStates.includes(reason)) reasons.set(ticket.id, reason);

  }
  return reasons;
}
export const projectRunAlerts = (runs: Row[]) => newestRuns(runs).filter(
  (run) => !run.ticket && attentionStates.includes(run.status || ""),
);
export const runSubject = (db: Workspace, run: Row) =>
  db.tickets.find((ticket) => ticket.id === run.ticket)?.name ||
  db.projects.find((project) => project.id === run.project)?.name || run.name;
export const options = (rows: Row[]) =>
  rows.map((r) => ({ value: r.id, label: r.name }));
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export async function request<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const resp = await fetch("/api/" + path, {
    method,
    signal: AbortSignal.timeout(30000),
    cache: method === "GET" && path === "workspace" ? "no-cache" : "no-store",
    headers: {
      "X-AgentBoard-UI": "1",
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text();
    let message = text;
    try {
      const detail = JSON.parse(text).detail;
      message =
        typeof detail === "string" ? detail : JSON.stringify(detail) || text;
    } catch (err) {
      if (!(err instanceof SyntaxError)) throw err;
    }
    throw new ApiError(resp.status, message || resp.statusText);
  }
  return resp.status === 204 ? (undefined as T) : (resp.json() as Promise<T>);
}
export function errorText(e: unknown) {
  return e instanceof Error ? e.message : "The request failed.";
}

export function projectTags(documents: Row[]) {
  const catalogs = documents.filter(row => row.document_type === "unclassified" && row.name.trim().toLowerCase() === "tag catalog");
  if (catalogs.length !== 1) return [];
  return (catalogs[0].content || "").split(/^## /m).slice(1).map(section => {
    const [heading, ...lines] = section.split("\n");
    const field = (name: string) => lines.find(line => line.startsWith(name + ": "))?.slice(name.length + 2).trim();
    const id = heading.trim();
    return { id, label: field("Label") || id, meaning: field("Meaning"), state: field("State") };
  });
}
