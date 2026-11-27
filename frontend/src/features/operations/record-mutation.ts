import { request, workspacePath, type Kind, type Row, type Workspace, type WorkspaceRefresh } from "../../model";
import { operations, projectResource } from "./operation-store";

export type RecordAction = "save" | "delete" | "restore" | "purge";
const same = (a: unknown, b: unknown) => JSON.stringify(Array.isArray(a) ? [...a].sort() : a ?? "") === JSON.stringify(Array.isArray(b) ? [...b].sort() : b ?? "");
export function recordMatches(row: Row, fields: Record<string, unknown>) { return Object.entries(fields).every(([key, value]) => same(row[key as keyof Row], value)); }
export function recordResources(kind: Kind, project: string, row?: Row) { return [projectResource(kind === "projects" ? row?.id || "new" : project)]; }

export async function mutateRecord(config: {
  kind: Kind; project: string; row?: Row; fields?: Record<string, unknown>; action: RecordAction;
  previousIds?: string[]; write: () => Promise<Row | void>; refresh: WorkspaceRefresh; confirmed?: () => void; settled?: () => void;
}) {
  const { kind, row, action, fields = {} } = config;
  const verificationProject = kind === "projects" ? "" : config.project;
  let saved: Row | void;
  function find(data: Workspace) {
    if (action === "purge") return !data.projects.some(item => item.id === row?.id);
    if (action === "delete") return !data[kind].some(item => item.id === row?.id) && data.trash.some(item => item.k === kind && item.r.id === row?.id);
    if (action === "restore") return data[kind].some(item => item.id === row?.id && item.revision > row.revision);
    return data[kind].some(item => saved
      ? item.id === saved.id && item.revision >= saved.revision
      : (row ? item.id === row.id && item.revision > row.revision : !config.previousIds?.includes(item.id)) && recordMatches(item, fields));
  }
  const label = action === "delete" || action === "purge" ? "Deleting" : action === "restore" ? "Restoring" : "Saving";
  const completed = action === "delete" || action === "purge" ? "Deleted" : action === "restore" ? "Restored" : "Saved";
  return operations.run<Row | void>({
    resources: recordResources(kind, config.project, row), label: label + " " + (row?.name || String(fields.name || "record")), completed,
    write: config.write,
    reconcile: async () => {
      const data = await request<Workspace>(workspacePath(verificationProject));
      if (!find(data)) throw new Error("The saved outcome is not yet confirmed.");
      return row ? data[kind].find(item => item.id === row.id) : data[kind].find(item => !config.previousIds?.includes(item.id) && recordMatches(item, fields));
    },
    confirmed: value => { saved = value; config.confirmed?.(); },
    sync: () => config.refresh(find, verificationProject),
    settled: config.settled,
  });
}
