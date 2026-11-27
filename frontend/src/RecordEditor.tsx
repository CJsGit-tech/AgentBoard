import { workspacePath } from "./model";
import { useEditorWorkspace } from "./features/workspace/editor-workspace";
import { OperationFeedback, useOperationLock } from "./features/operations/Operations";
import { operations, conflicts, inFlight } from "./features/operations/operation-store";
import { mutateRecord, recordResources, type RecordAction } from "./features/operations/record-mutation";
import type { WorkspaceRefresh } from "./model";
import { useEffect, useId, useLayoutEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import {
  Alert,
  Button,
  Checkbox,
  Drawer,
  Group,
  Menu,
  NativeSelect,
  MultiSelect,
  Stack,
  Tabs,
  TextInput,
  Textarea,
} from "@mantine/core";
import { ReviewHistory } from "./features/monitoring/ReviewHistory";
import { useActivityPage, ActivityPageContents } from "./features/monitoring/activity-page";
import { Empty, History, Item, Tag } from "./Common";
import RichTextEditor from "./features/documents/RichTextEditor";
import { Markdown } from "./features/documents/Markdown";
import { TicketSummary } from "./features/tickets/TicketSummary";
import { TicketReader } from "./features/tickets/TicketReader";
import { CriteriaEditor } from "./features/tickets/CriteriaEditor";
import { ticketsForMilestone } from "./features/tickets/milestone";
import { ProjectResources } from "./ProjectResources";
import { ProjectDeletion } from "./ProjectDeletion";
import { RunReport } from "./features/monitoring/RunReport";
import { describeWithHelp, InfoHelp } from "./features/help/InfoHelp";
import "./features/forms/actions.css";
import { SubmissionGate } from "./formActions";
import {
  type Workspace,
  type Row,
  type Kind,
  type Editor,
  type TicketCriterion,
  ApiError,
  errorText,
  single,
  nameOf,
  options,
  statuses,
  runStates,
  request,
  stamp,
  documentTypes,
  workTypes,
  latestEditor,
  projectTags,
  currentReview,
} from "./model";

type Draft = Record<string, string | string[] | TicketCriterion[]>;
const pendingDrafts = new Map<string, {initial:Draft;draft:Draft}>();
function fields(
  kind: Kind,
  r: Partial<Row>,
  project: string,
  db: Workspace,
): Draft {
  const base = { name: r.name || "" };
  switch (kind) {
    case "projects":
      return { ...base, description: r.description || "", checkout_path: r.checkout_path || "" };
    case "milestones":
      return { ...base, project, description: r.description || "" };
    case "roles":
      return {
        ...base,
        project,
        description: r.description || "",
        instructions: r.instructions || "",
      };
    case "documents":
      return {
        ...base, project, tags: r.tags || [], description: r.description || "",
        document_type: r.document_type || "unclassified", content: r.content || "",
        source_documents: r.source_documents || [],
      };
    case "tickets":
      return {
        ...base,
        project,
        tags: r.tags || [],
        milestone:
          r.milestone ||
          db.milestones.find((m) => m.project === project)?.id ||
          "",
        description: r.description || "",
        role: r.role || "",
        status: r.status || "Planned",
        due: r.due || "",
        documents: r.documents || [],
        output_documents: r.output_documents || [],
        criteria: r.criteria || [],
        work_type: r.work_type || "UNCLASSIFIED",
        execution_role: r.execution_role || "",
      };
    case "runs":
      return {
        ...base,
        project,
        agent: r.agent || "Codex",
        status: r.status || "Running",
        ticket: r.ticket || "",
        note: r.note || "",
        mode: r.mode || "Edit",
      };
  }
}
type Props = {
  db: Workspace;
  editor: Editor;
  scope: string;
  close: () => void;
  open: (s: Editor) => void;
  refresh: WorkspaceRefresh;
  inline?: boolean;
};
export function RecordEditor({
  db: parentDB,
  editor,
  scope,
  close: closeParent,
  open,
  refresh,
  inline = false,
}: Props) {
  const { kind: k, row } = editor;
  const sourceInputId = useId(), sourceHelpId = useId();
  const opener=useRef(document.activeElement as HTMLElement|null);
  function close(){
    closeParent();
    requestAnimationFrame(()=>{
      if(opener.current?.isConnected)opener.current.focus({preventScroll:true});
      else if(document.activeElement===document.body){
        const heading=document.querySelector<HTMLElement>("main h1,main h2");
        heading?.setAttribute("tabindex","-1");heading?.focus({preventScroll:true});
      }
    });
  }
  const initialProject = row?.project || editor.project || scope || parentDB.projects[0]?.id || "";
  const draftKey=k+":"+(row?.id||initialProject);
  const retained=pendingDrafts.get(draftKey);
  const [initial] = useState(() => retained?.initial || fields(k, row || {}, initialProject, parentDB)),
    [draft, setDraft] = useState<Draft>(retained?.draft || initial);
  const p = String(draft.project || "");
  const project = k === "projects" ? row?.id || "" : p || initialProject;
  const needsProject = !!project && !parentDB.projects.some(item => item.id === project && !item.summary);
  const related = useEditorWorkspace(needsProject ? workspacePath(project) : undefined);
  const directory = useEditorWorkspace(!row && k !== "projects" ? workspacePath("") : undefined);
  const db = related.data || parentDB;
  const projectOptions = directory.data?.projects || parentDB.projects;
  const waitingForProject = needsProject && !related.data;
  useEffect(() => {
    if (!row && k === "tickets" && !draft.milestone && related.data) {
      const milestone = related.data.milestones.find(item => item.project === p);
      if (milestone) setDraft(current => current.project === p && !current.milestone ? { ...current, milestone: milestone.id } : current);
    }
  }, [related.data, k, p, row, draft.milestone]);
  const mounted=useRef(true);
  useEffect(()=>()=>{mounted.current=false;},[]);
  const [localBusy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [conflict, setConflict] = useState(false);
  const resources = recordResources(k, project, row);
  const locked = useOperationLock(resources);
  const busy = localBusy || locked;
  const repairable=locked&&!operations.getSnapshot().some(op=>conflicts(op.resources,resources)&&inFlight(op));
  function retainDraft(){pendingDrafts.set(draftKey,{initial,draft});}
  function savedAndClose(){pendingDrafts.delete(draftKey);if(mounted.current)close();}
  const [discard, setDiscard] = useState<{ action: () => void } | null>(null);
  const [editorRole, setEditorRole] = useState("");
  const existingRun = k === "runs" && !!row;
  const existingTicket = k === "tickets" && !!row;
  const [panel, setPanel] = useState<string | null>(editor.panel || (existingRun || existingTicket ? "Summary" : "Details"));
  const [confirmProjectDeletion, setConfirmProjectDeletion] = useState(false);
  const deleteButton = useRef<HTMLButtonElement>(null);
  const editedField = useRef<HTMLElement | null>(null);
  const recordForm=useRef<HTMLFormElement>(null),actionBar=useRef<HTMLDivElement>(null);
  useLayoutEffect(()=>{const bar=actionBar.current,form=recordForm.current;if(!bar||!form)return;const measure=()=>form.style.setProperty("--record-actions-height",bar.getBoundingClientRect().height+"px");measure();const observer=new ResizeObserver(measure);observer.observe(bar);return()=>observer.disconnect();},[panel]);
  const mutationGate=useRef(new SubmissionGate());
  function cancelProjectDeletion() {
    setConfirmProjectDeletion(false);
    requestAnimationFrame(() => deleteButton.current?.focus());
  }
  const dirty = JSON.stringify(initial) !== JSON.stringify(draft);
  useEffect(() => {
    if (!dirty && !busy) return;
    function beforeUnload(e: BeforeUnloadEvent) {
      e.preventDefault();
      e.returnValue = "";
    }
    function beforeNavigate(e: Event) {
      if (repairable) { retainDraft(); return; }
      if (busy || (dirty && !window.confirm("Discard your unsaved changes?"))) {
        e.preventDefault();
        requestAnimationFrame(() => editedField.current?.focus());
      }
    }
    window.addEventListener("beforeunload", beforeUnload);
    window.addEventListener("agentboard:before-navigate", beforeNavigate);
    return () => {
      window.removeEventListener("beforeunload", beforeUnload);
      window.removeEventListener("agentboard:before-navigate", beforeNavigate);
    };
  }, [dirty, busy, repairable, draft]);
  function leave(action: () => void) {
    if(repairable){retainDraft();action();return;}
    if (!busy) {
      if (dirty) { if (document.activeElement?.matches("input,textarea,select,[contenteditable]")) editedField.current = document.activeElement as HTMLElement; setDiscard({ action }); }
      else action();
    }
  }
  const current = (key: string) => String(draft[key] ?? "");
  const set = (key: string, v: string | string[] | TicketCriterion[]) => {
    if (!operations.locked(resources)) setDraft((d) => ({ ...d, [key]: v }));
  };
  const choices = (kind: Kind) =>
    options(db[kind].filter((r) => r.project === p));
  const availableTags = projectTags(db.documents.filter(doc => doc.project === p))
    .filter(entry => entry.state === "Active").map(entry => entry.id);
  const live = row ? db[k].find((r) => r.id === row.id) : undefined;
  const stale = !!row && live?.revision !== row.revision;
  async function submit(ev: FormEvent) {
    ev.preventDefault();
    if (waitingForProject || mutationGate.current.busy || operations.locked(resources)) return;
    if (stale) { setError("Load the latest revision before saving. Your draft is still here."); return; }
    if (
      !current("name").trim() ||
      (k === "documents" && !current("content").trim())
    ) {
      setError("Complete the required fields.");
      requestAnimationFrame(() => (document.querySelector<HTMLElement>("[data-record-form] :invalid") || document.querySelector<HTMLElement>("[data-record-form] .rte-editable, [data-record-form] .rte-source"))?.focus());
      return;
    }
    if ((k === "projects" ? parentDB.projects : db[k]).some(other => other.id !== row?.id && (k === "projects" || other.project === p) && other.name.trim().toLocaleLowerCase() === current("name").trim().toLocaleLowerCase())) { setError("A "+single[k]+" with this name already exists. Choose another name."); return; }
    const changes = Object.fromEntries(
      Object.entries(draft)
        .filter(
          ([key, value]) =>
            !row || JSON.stringify(initial[key]) !== JSON.stringify(value),
        )
        .map(([key, value]) => [
          key,
          typeof value === "string" && key !== "content" ? value.trim() : value,
        ]),
    );
    if (row && Object.keys(changes).length === 0) {
      close();
      return;
    }
    const actorQuery = editorRole ? "?editor_role_id=" + encodeURIComponent(editorRole) : "";
    await execute(() =>
      row
        ? request(k + "/" + encodeURIComponent(row.id) + actorQuery, "PATCH", {
            revision: row.revision,
            changes,
          })
        : request(k + actorQuery, "POST", changes), "save", changes);
  }
  async function execute(mutate: () => Promise<import("./model").Row | void>, action: RecordAction = "save", values: Record<string,unknown> = {}) {
    if (operations.locked(resources)) return;
    return mutationGate.current.run(async () => {
      setBusy(true); setError("");
      try {
        await mutateRecord({kind:k,project,row,fields:values,previousIds:db[k].map(item=>item.id),action,write:mutate,refresh,confirmed:savedAndClose});
      } catch (err) {
        setError(errorText(err));
        setConflict(err instanceof ApiError && (err.status===404 || (err.status===409 && err.message.includes("revision"))));
        requestAnimationFrame(()=>editedField.current?.focus());
      } finally { setBusy(false); }
    });
  }

  function input(
    key: string,
    label: string,
    multiline = false,
    required = false,
  ) {
    const props = {
      label,
      required,
      value: current(key),
      onChange: (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
      ) => set(key, e.currentTarget.value),
    };
    return multiline ? (
      <Textarea {...props} autosize minRows={3} maxRows={14} />
    ) : (
      <TextInput {...props} />
    );
  }
  function select(
    key: string,
    label: string,
    data: (string | { value: string; label: string })[],
    required = false,
  ) {
    return (
      <NativeSelect
        label={label}
        required={required}
        value={current(key)}
        onChange={(e) => set(key, e.currentTarget.value)}
        data={data}
      />
    );
  }
  const links: { kind: Kind; row: Row; label: string }[] = [];
  if (row && (k === "roles" || k === "milestones")) {
    const tickets = k === "milestones" ? ticketsForMilestone(db.tickets, row) : db.tickets.filter(t => t.project === row.project && t.role === row.id);
    tickets.forEach(t => links.push({kind:"tickets",row:t,label:"Ticket"}));
  }
  if (row && k === "tickets") {
    db.runs.filter((r) => r.ticket === row.id)
      .forEach((r) => links.push({ kind: "runs", row: r, label: "Run" }));
  }
  const relations = [
    { field: "documents", label: "Context" },
    { field: "output_documents", label: "Output" },
  ] as const;
  if (row && (k === "tickets" || k === "documents")) {
    for (const { field, label } of relations) {
      if (k === "tickets") {
        db.documents.filter((d) => row[field]?.includes(d.id))
          .forEach((r) => links.push({ kind: "documents", row: r, label }));
      } else {
        db.tickets.filter((t) => t[field]?.includes(row.id))
          .forEach((r) => links.push({ kind: "tickets", row: r, label }));
      }
    }
  }
  if (row && k === "runs") {
    const ticket = db.tickets.find((t) => t.id === row.ticket);
    if (ticket) links.push({ kind: "tickets", row: ticket, label: "Ticket" });
  }
  const showHistory = panel === "History" || (existingRun && panel === "Summary");
  const history = useActivityPage(row && showHistory ? (k === "projects" ? row.id : row.project) : undefined,
    {record: row?.id || "", action: panel === "Summary" ? "Created" : ""}, db.activity_count);
  return (
    <RecordSurface
      inline={inline}
      opened
      onClose={() => {
        if (confirmProjectDeletion) {
          if(repairable)leave(close);else if (!busy) cancelProjectDeletion();
        } else {
          leave(close);
        }
      }}
      title={confirmProjectDeletion ? "Permanently delete project?" : existingRun && panel !== "Details" ? "Run report" : existingTicket && panel !== "Details" ? row.name : (row ? "Edit " : "New ") + single[k]}
      position="right"
      size="min(490px, 95vw)"
      padding="lg"
      closeButtonProps={{ "aria-label": "Close editor" }}
      overlayProps={{ opacity: 0.6 }}
    >
      {!inline && <OperationFeedback />}
      {waitingForProject && !related.error && <p role="status">Loading project details…</p>}
      {(related.error || directory.error) && <Alert color="red" role="alert">
        {related.error || directory.error} <button className="link" onClick={related.error ? related.retry : directory.retry}>Retry</button>
      </Alert>}
      {confirmProjectDeletion && row ? <ProjectDeletion
        id={row.id}
        busy={busy}
        setBusy={setBusy}
        cancel={cancelProjectDeletion}
        row={row}
        refresh={refresh}
        deleted={savedAndClose}
      /> : <>
      {row && k === "tickets" && panel === "Details" && <TicketSummary db={db} ticket={row} status/>}
      {discard && (
        <Alert color="yellow" title="Discard your unsaved changes?" mb="md">
          <Group>
            <Button size="xs" onClick={() => { setDiscard(null); requestAnimationFrame(() => editedField.current?.focus()); }}>
              Keep editing
            </Button>
            <Button variant="subtle" size="xs" onClick={discard.action}>
              Discard changes
            </Button>
          </Group>
        </Alert>
      )}
      {error && (
        <Alert color="red" mb="md" role="alert">
          {error}
        </Alert>
      )}
      {(conflict || stale) && (
        <Alert color="yellow" mb="md">
          This record changed since you opened it. Your draft is still here.
          {live && (
            <Button
              size="compact-xs"
              variant="subtle"
              onClick={() => leave(() => open({ kind: k, row: live }))}
            >
              Load latest version
            </Button>
          )}
        </Alert>
      )}
      <Tabs value={panel} onChange={setPanel} keepMounted={false} className="editor-tabs">
        {row && <Tabs.List>
          {(existingRun || existingTicket) && <Tabs.Tab value="Summary">Summary</Tabs.Tab>}
          <Tabs.Tab value="Details">{existingRun ? "Edit report" : existingTicket ? "Edit ticket" : "Details"}</Tabs.Tab>
          <Tabs.Tab value="Links">Links</Tabs.Tab><Tabs.Tab value="History">History</Tabs.Tab>
        </Tabs.List>}
        {existingRun && row && <Tabs.Panel value="Summary">
          <ActivityPageContents page={history}>
          <RunReport db={db} run={live || row} history={history.items} openTicket={ticket => leave(() => open({kind: "tickets", row: ticket}))} />
          </ActivityPageContents>
        </Tabs.Panel>}
        {existingTicket && row && <Tabs.Panel value="Summary">
          <TicketReader db={db} ticket={live || row} openRun={run => leave(() => open({kind: "runs", row: run}))} />
        </Tabs.Panel>}
      <Tabs.Panel value="Details">
      {k !== "projects" && !db.projects.length ? (
        <>
          <Empty>Create a project first.</Empty>
          <Button onClick={() => open({ kind: "projects" })}>
            New project
          </Button>
        </>
      ) : (
        <form ref={recordForm} data-record-form onSubmit={submit} onFocusCapture={event=>{if((event.target as HTMLElement).matches("input,textarea,select,[contenteditable]"))editedField.current=event.target as HTMLElement;}}>
          <div ref={actionBar} className="record-actionbar">
            <Button type="button" variant="default" onClick={() => leave(close)} disabled={busy&&!repairable}>{repairable?"Close editor":"Cancel"}</Button>
              {row && <Menu position="bottom-end"><Menu.Target><Button type="button" variant="default" disabled={busy}>More actions</Button></Menu.Target><Menu.Dropdown>
                <Menu.Item
                  ref={k === "projects" ? deleteButton : undefined}
                  type="button"
                  color="red"
                  disabled={busy || stale}
                  onClick={() => {
                    if (k === "projects") {
                      setConfirmProjectDeletion(true);
                      return;
                    }
                    if (k === 'documents' && currentReview(db, row.id)?.operation !== 'Delete') {
                      void operations.run({resources,label:"Requesting removal review",completed:"Review requested",
                        write:()=>request('reviews/start/documents/'+row.id,'POST',{revision:row.revision,operation:'Delete',request:'Remove '+row.name+' from the project requirements.'}),
                        reconcile:async()=>{const data=await request<Workspace>(workspacePath(p));if(!data.reviews.some(v=>v.subject===row.id&&!v.superseded&&v.operation==='Delete'))throw Error('Review not confirmed');},
                        sync:()=>refresh(data=>data.reviews.some(v=>v.subject===row.id&&!v.superseded&&v.operation==='Delete')),
                        confirmed:()=>setError('Ask your agent to check the linked documents before removal. Findings and your scope decision are logged in Runs & activity.')
                      }).catch(err=>setError(errorText(err)));
                      return;
                    }
                    void execute(() =>
                      request(
                        k +
                          "/" +
                          encodeURIComponent(row.id) +
                          "?revision=" +
                          row.revision,
                        "DELETE",
                      ), "delete",
                    );
                  }}
                >
                  {k === "projects" ? "Delete project" : "Delete"}
                </Menu.Item>
              </Menu.Dropdown></Menu>}
              <Button
                className="save"
                type="submit"
                loading={busy}
                disabled={waitingForProject || busy || stale || (k === "tickets" && !draft.milestone)}
              >
                {k === "runs" ? "Save report" : "Save " + single[k]}
              </Button>
          </div>
          <fieldset aria-busy={busy} disabled={busy} style={{border:0,padding:0,margin:0,minWidth:0}}>
          <legend className="sr-only">Record fields</legend><Stack gap="sm">
            {k !== "projects" &&
              (row ? (
                <small>Project · {nameOf(db, "projects", p)}</small>
              ) : (
                <NativeSelect
                  label="Project"
                  required
                  value={p}
                  onChange={(e) => {
                    const next = e.currentTarget.value;
                    setEditorRole("");
                    setDraft((d) => ({
                      ...d,
                      project: next,
                      ...("tags" in d ? { tags: [] } : {}),
                      ...("source_documents" in d ? { source_documents: [] } : {}),
                      ...(k === "tickets"
                        ? {
                            milestone:
                              db.milestones.find((m) => m.project === next)
                                ?.id || "",
                            role: "",
                            documents: [],
                            output_documents: [],
                            criteria: [],
                          }
                        : k === "runs"
                          ? { ticket: "" }
                          : {}),
                    }));
                  }}
                  data={options(projectOptions)}
                />
              ))}
            {row && (k === "tickets" || k === "documents") && (
              <Stack gap={2}>
                <small>Created at · {stamp(row.created_at)}</small>
                <small>Updated at · {stamp(row.updated_at)}</small>
                <small>{row.latest_edit_role ? "Latest edit role" : "Latest editor"} · {latestEditor(row)}</small>
              </Stack>
            )}
            {input("name", "Name", false, true)}
            {k === "documents" && select("document_type", "Document type", documentTypes)}
            {k === "tickets" && select("work_type", "Ticket type", workTypes)}
            {"tags" in draft && (availableTags.length || draft.tags.length) ? (
              <MultiSelect label="Managed tags" searchable data={[...new Set([...availableTags, ...(draft.tags as string[])])]}
                value={draft.tags as string[]} onChange={v => set("tags", v)} />
            ) : null}
            {row && <a href={`#${k}/${row.id}`}>Record link</a>}
            {k === "projects" && input("checkout_path", "Local checkout path (optional)")}
            {"description" in draft &&
              input("description", "Description", true)}
            {k === "roles" &&
              input("instructions", "Reusable instructions", true)}
            {k === "documents" && <RichTextEditor disabled={busy} value={current("content")} onChange={value=>set("content",value)} render={text=><Markdown text={text}/>} invalid={!!error&&!current("content").trim()}/>}
            {k === 'documents' && <div><div className="field-info"><label htmlFor={sourceInputId}>Source documents</label><InfoHelp label="source documents" id={sourceHelpId}>Changes to these documents trigger an impact review.</InfoHelp></div><MultiSelect id={sourceInputId} ref={describeWithHelp(sourceHelpId)} searchable
              data={choices('documents').filter(doc => doc.value !== row?.id)} value={draft.source_documents as string[]} onChange={value => set('source_documents', value)} /></div>}
            {k === "tickets" && (
              <>
                {select("milestone", "Milestone", choices("milestones"), true)}
                {!choices("milestones").length && (
                  <Alert color="yellow">
                    Create a milestone in this project before adding a ticket.{" "}
                    <button
                      type="button"
                      className="link"
                      onClick={() =>
                        leave(() => open({ kind: "milestones", project: p }))
                      }
                    >
                      New milestone
                    </button>
                  </Alert>
                )}
                {select("status", "Status", statuses)}
                {select("execution_role", "Execution role", [{ value: "", label: "Unspecified" }, "FE", "BE"])}
                {select("role", "Assigned role", [
                  { value: "", label: "Unassigned" },
                  ...choices("roles"),
                ])}
                <TextInput
                  label="Due date"
                  type="date"
                  value={current("due")}
                  onChange={(e) => set("due", e.currentTarget.value)}
                />
                {choices("documents").length ? relations.map(({ field, label }) => (
                  <Checkbox.Group
                    key={field}
                    label={label + " documents"}
                    description={field === "documents" ? "Requirements and approved inputs." : "Reports and captures produced by the work."}
                    value={draft[field] as string[]}
                    onChange={(value) => set(field, value)}
                  >
                    <Stack gap={5} mt={5}>
                      {choices("documents").map((d) => (
                        <Checkbox key={d.value} value={d.value} label={d.label} />
                      ))}
                    </Stack>
                  </Checkbox.Group>
                )) : <small>No documents in this project.</small>}
                <CriteriaEditor documents={db.documents.filter(document => document.project === p)}
                  outputIds={draft.output_documents as string[]} value={draft.criteria as TicketCriterion[]} onChange={value => set("criteria", value)} />
              </>
            )}
            {k === "runs" && (
              <>
                {select("agent", "Agent", ["Codex", "Claude", "InApp Assistant"])}
                {select('mode', 'Run mode', ['Edit', 'Read only'])}
                {select("ticket", "Linked ticket", [
                  { value: "", label: "Project-level run" },
                  ...choices("tickets"),
                ])}
                {select("status", "Reported status", runStates)}
                {input("note", "Latest report", true)}
                {row?.updated && (
                  <small>Last report · {stamp(row.updated)}</small>
                )}
              </>
            )}
            {(k === "tickets" || k === "documents") && choices("roles").length > 0 && (
              <NativeSelect
                label="Edit as role"
                value={editorRole}
                onChange={(e) => setEditorRole(e.currentTarget.value)}
                data={[{ value: "", label: "No project role" }, ...choices("roles")]}
              />
            )}

          </Stack>
          </fieldset>
        </form>
      )}
      {k === "projects" && row && !waitingForProject && <ProjectResources db={db} project={row.id}/>}
      </Tabs.Panel>
      {row && <>
        <Tabs.Panel value="Links">
          <h3 className="detail">Linked records</h3>
          {!links.length && <Empty>No linked records.</Empty>}
          {links.map((link) => link.kind === "tickets" ? <div className="log" key={link.label+link.row.id}><small>{link.label}</small><TicketSummary db={db} ticket={link.row} open={()=>leave(()=>open(link))} status/></div> : (
            <Item
              key={link.label + link.row.id}
              row={link.row}
              onClick={() => link.kind === "documents"
                ? (location.hash = "documents/" + link.row.id)
                : leave(() => open(link))}
              left={<small>{link.label}</small>}
              right={link.row.status ? <Tag value={link.row.status} /> : null}
            />
          ))}
        </Tabs.Panel>
        <Tabs.Panel value="History">
          <h3 className="detail">Change history</h3>
          {row?.project && (k === "tickets" || k === "documents") && <ReviewHistory key={row.id} project={row.project} subject={row.id} />}
          <ActivityPageContents page={history}>
          {history.items.map((l) => (
            <History key={l.id} entry={l} db={db} />
          ))}
          {!history.items.length && <Empty>No recorded changes.</Empty>}
          </ActivityPageContents>
        </Tabs.Panel>
      </>}
      </Tabs>
      </>}
    </RecordSurface>
  );
}

function RecordSurface({inline,children,...props}:React.ComponentProps<typeof Drawer>&{inline?:boolean}) {
 return inline ? <section className="inline-record" aria-label={String(props.title || "Record editor")}>{children}</section> : <Drawer {...props}>{children}</Drawer>;
}
