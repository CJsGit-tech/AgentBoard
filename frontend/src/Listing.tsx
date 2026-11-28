import { workspacePath } from "./model";
import { useOperations } from "./features/operations/Operations";
import { operations, projectResource } from "./features/operations/operation-store";
import { mutateRecord } from "./features/operations/record-mutation";
import type { WorkspaceRefresh } from "./model";
import { useRef, useState, type ReactNode } from "react";
import { Alert, Button, Menu, NativeSelect, Popover, TextInput } from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { Empty, Icon, Tag } from "./Common";
import { Directory } from "./features/directory/Directory";
import { TicketSummary } from "./features/tickets/TicketSummary";
import { ticketsForMilestone } from "./features/tickets/milestone";
import { proofHref, resolveProof } from "./features/tickets/proof-links";
import { CompletionDial } from "./Dashboard";
import { statusFill, statusShape, type Status } from "./features/charts/primitives";
import { DocumentLibrary } from "./DocumentLibrary";
import { useActivityPage, ActivityPageContents } from "./features/monitoring/activity-page";
import { ActivityTimeline, RunList, type RunGrouping } from "./Monitoring";
import {
  type Workspace, type Page, type Row, type Change, type Editor, type TicketView,
  nameOf, names, scoped, statuses, runStates, options, shortDate, stamp, percent, done,
  dueSoon, isOverdue, localDate, documentTypes, workTypes, latestEditor,
  attentionReasons, projectRunAlerts, runSubject, request, errorText,
} from "./model";

type TicketGrouping = "Milestone" | "Status" | "Type" | "None";
type ListPage = Exclude<Page, "dashboard" | "canvas" | "assistant" | "portfolio">;
type Props = {
  documentId?: string; db: Workspace; page: ListPage; scope: string; milestoneFilter: string; initialTicketView: TicketView;
  edit: (editor: Editor) => void; inspect: (entry: Change) => void; milestone: (id: string) => void;
  onMilestoneFilter: (id: string) => void; onNewTicket: () => void;
  showMonitoring: (page: Page) => void; refresh?: WorkspaceRefresh;
};
type Choice = { value: string; label: string };
type Filter = { label: string; value: string; change: (value: string) => void; data: (string | Choice)[] };
const all = (label: string) => ({ value: "", label });
const workType = (row: Row) => row.work_type === "BUILD" ? "Build" : row.work_type === "BUG" ? "Bug" : "Unclassified";
const dateLabel = (row: Row) => isOverdue(row) ? "Overdue" : row.due === localDate() ? "Due today" : "Due " + shortDate(row.due);
const evidenceStates = ["Verified proof", "Missing required proof", "Linked outputs", "No evidence linked"] as const;

function evidenceForTicket(db: Workspace, ticket: Row) {
  const links = new Map<string, string>();
  let missingRequired = false;
  for (const criterion of ticket.criteria || []) {
    let hasProof = false;
    for (const proof of criterion.evidence || []) {
      if (proof.status !== "verified") continue;
      const document = resolveProof(db, ticket, proof);
      if (!document) continue;
      hasProof = true;
      links.set(proofHref(proof), proof.kind === "screenshot" ? proof.filename : document.name);
    }
    if (criterion.evidence_required && !hasProof) missingRequired = true;
  }
  const verified = links.size > 0;
  for (const document of db.documents) {
    if (!verified && document.project === ticket.project && ticket.output_documents?.includes(document.id)) {
      links.set(`#documents/${encodeURIComponent(document.id)}`, document.name);
    }
  }
  return { state: evidenceStates[missingRequired ? 1 : verified ? 0 : links.size ? 2 : 3], links };
}

function TicketEvidence({ evidence }: { evidence?: ReturnType<typeof evidenceForTicket> }) {
  if (!evidence || evidence.state === "No evidence linked") return null;
  const links = [...evidence.links];
  return <div className="ticket-evidence" onClick={event => event.stopPropagation()}>
    <span>{evidence.state}</span>
    {links.length === 1 && <a href={links[0][0]}>{links[0][1]}</a>}
    {links.length > 1 && <details><summary>View {links.length} links</summary><ul>
      {links.map(([href, name]) => <li key={href}><a href={href}>{name}</a></li>)}
    </ul></details>}
  </div>;
}

function RecordTable({ headers, groups, makeCells, onOpen, collapse, toggle }: {
  headers: string[]; groups: { key: string; label?: string; rows: Row[]; summary?: ReactNode }[];
  makeCells: (row: Row) => ReactNode[]; onOpen: (row: Row) => void;
  collapse?: Set<string>; toggle?: (key: string) => void;
}) {
  return <div className="tablebox"><table className="record-table">
    <thead><tr>{headers.map((header) => <th scope="col" key={header}>{header}</th>)}</tr></thead>
    {groups.map((group) => <tbody key={group.key}>
      {group.label && <tr><th scope="rowgroup" colSpan={headers.length} className="row-group">
        {toggle ? <button className="row-group-label" aria-expanded={!collapse?.has(group.key)} onClick={() => toggle(group.key)}>
          <span className={collapse?.has(group.key) ? "folder-caret" : "folder-caret open"} aria-hidden="true" />{group.label}{group.summary}
        </button> : <span className="row-group-label">{group.label}{group.summary}</span>}
      </th></tr>}
      {!collapse?.has(group.key) && group.rows.map((row) => <tr className="row" key={row.id} onClick={() => onOpen(row)}>
        {makeCells(row).map((cell, i) => <td key={i} data-label={headers[i]}>{cell}</td>)}
      </tr>)}
    </tbody>)}
  </table></div>;
}

export function Listing({ documentId, db, page: k, scope, milestoneFilter: mil, initialTicketView, edit, inspect, milestone, onMilestoneFilter, onNewTicket, showMonitoring, refresh }: Props) {
  const [query, search] = useState("");
  const [status, setStatus] = useState(initialTicketView === "attention" ? "Needs attention" : "");
  const [due, setDue] = useState(initialTicketView === "overdue" ? "Overdue" : "");
  const [role, setRole] = useState("");
  const [evidenceState, setEvidenceState] = useState("");
  const [tag, setTag] = useState("");
  const [type, setType] = useState("");
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");
  const [period, setPeriod] = useState("");
  const [layout, setLayout] = useState("Board");
  const [savedMoves, saveMoves] = useState<Record<string, Row>>({});
  const [moving, setMoving] = useState("");
  const [moveFailure, failMove] = useState<{row:Row;status:string;message:string}|null>(null);
  const [announcement, announce] = useState("");
  const [dropTarget, setDropTarget] = useState("");
  const dragging = useRef("");
  const movementPending = useRef(false);
  const ticketRows = db.tickets.map(row => savedMoves[row.id]?.revision > row.revision ? savedMoves[row.id] : row);
  useOperations();
  async function moveTicket(row:Row, nextStatus:string, retry=false) {
    if (movementPending.current || operations.locked([projectResource(row.project || scope)]) || row.status===nextStatus) return;
    movementPending.current=true; setMoving(row.id); failMove(null);
    try {
      if (retry) { const workspace=await request<Workspace>(workspacePath(row.project || scope)); const latest=workspace.tickets.find(t=>t.id===row.id); if(!latest || latest.revision!==row.revision) { await refresh?.(); throw new Error("This ticket changed. Review its latest status before moving it again."); } }
      await mutateRecord({kind:"tickets",project:row.project||scope,row,fields:{status:nextStatus},action:"save",refresh:refresh||(async()=>{}),
        write:async()=>{
          const saved=await request<Row>("tickets/"+encodeURIComponent(row.id),"PATCH",{revision:row.revision,changes:{status:nextStatus}});
          saveMoves(old=>({...old,[saved.id]:saved}));return saved;
        },
        settled:()=>{
          if(status && status!==nextStatus)setStatus("");
          if(due && nextStatus==="Done")setDue("");
          setCollapsed(new Set());announce(`${row.name}: ${row.status} to ${nextStatus}.`);
          requestAnimationFrame(()=>{ const target=document.querySelector<HTMLElement>(`[data-ticket="${CSS.escape(row.id)}"] .ticket-name`); target?.scrollIntoView({block:"nearest"});target?.focus(); });
        }});
    } catch(error) { failMove({row,status:nextStatus,message:errorText(error)}); announce("Ticket move failed. Previous position retained."); }
    finally { movementPending.current=false;setMoving("");setDropTarget(""); }
  }
  const [ticketGroup, setTicketGroup] = useLocalStorage<TicketGrouping>({ key: "agentboard.ui.tickets.group", defaultValue: "Milestone" });
  const [boardGroup, setBoardGroup] = useLocalStorage<TicketGrouping>({ key: "agentboard.ui.board.group", defaultValue: "Status" });
  const documentGroup = "Family" as const;
  const [runGroup, setRunGroup] = useLocalStorage<RunGrouping>({ key: "agentboard.ui.runs.group.v5", defaultValue: "Day" });
  const [audit, showAudit] = useLocalStorage({ key: "agentboard.ui.edit-metadata", defaultValue: false });
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());
  const [doneAll, setDoneAll] = useState(false);
  const board = k === "tickets" && layout === "Board";
  const monitoring = k === "runs" || k === "activity";
  const tickets = scoped(ticketRows, scope, "tickets");
  const runs = scoped(db.runs, scope, "runs");
  const milestones = scoped(db.milestones, scope, "milestones");
  const selectedMilestone = mil ? milestones.find(record => record.id === mil) : undefined;
  const milestoneTickets = selectedMilestone ? ticketsForMilestone(tickets, selectedMilestone) : [];
  const ticketCohort = selectedMilestone ? milestoneTickets : mil ? [] : tickets;
  const evidenceByTicket = new Map(k === "tickets" ? tickets.map(ticket => [ticket.id, evidenceForTicket(db, ticket)]) : []);
  const attention = k === "tickets" ? attentionReasons(tickets, runs) : new Map<string, string>();
  const term = query.trim().toLowerCase();
  const matches = (values: (string | undefined)[]) => !term || values.some((value) => value?.toLowerCase().includes(term));
  const needsAttention = k === "tickets" && status === "Needs attention";
  const rows = k === "activity" ? [] : (k === "tickets" ? ticketCohort : scoped(db[k], scope, k)).filter((row) =>
    matches([row.name, row.id, row.description, row.agent, row.note, row.content, row.work_type, row.document_type,
      nameOf(db, "projects", row.project), k === "runs" ? runSubject(db, row) : undefined]) &&
    (!type || (k === "documents" ? row.document_type || "unclassified" : row.work_type || "UNCLASSIFIED") === type) &&
    (!tag || row.tags?.includes(tag)) &&
    (!status || (needsAttention ? attention.has(row.id) : row.status === status)) &&
    (!role || row.role === role) && (!evidenceState || evidenceByTicket.get(row.id)?.state === evidenceState) &&
    (!due || (due === "No date" ? !row.due : due === "Overdue" ? isOverdue(row) : dueSoon(row) && !isOverdue(row))),
  );
  const activity = useActivityPage(k === "activity" ? scope : undefined, {
    actor, action, kind: type, search: query.trim(),
    start: period ? new Date(localDate(Number(period)) + "T00:00:00").toISOString() : "",
    end: period ? new Date(localDate(1) + "T00:00:00").toISOString() : "",
  }, db.activity_count);
  const alerts = needsAttention && !tag && !mil && !role && !type && !due && !evidenceState ? projectRunAlerts(runs).filter((run) =>
    matches([run.name, run.agent, run.note, runSubject(db, run)])) : [];

  const filters: Filter[] = [];
  if (k === "tickets" || k === "runs") filters.push({ label: "Status", value: status, change: setStatus,
    data: [all("All statuses"), ...(k === "runs" ? runStates : [...statuses, "Needs attention"])] });
  if (k === "tickets" || k === "documents") filters.push({ label: k === "tickets" ? "Ticket type" : "Document type",
    value: type, change: setType, data: [all("All types"), ...(k === "tickets" ? workTypes : documentTypes)] });
  if (k === "tickets" || k === "documents") {
    const tags = [...new Set(scoped(db[k], scope, k).flatMap(row => row.tags || []))].sort();
    if (tags.length || tag) filters.push({ label: "Tag", value: tag, change: setTag, data: [all("All tags"), ...tags] });
  }
  if (k === "tickets") filters.push(
    { label: "Milestone", value: mil, change: onMilestoneFilter, data: [all("All milestones"), ...options(milestones)] },
    { label: "Role", value: role, change: setRole, data: [all("All roles"), ...options(scoped(db.roles, scope, "roles"))] },
    { label: "Due date", value: due, change: setDue, data: [all("Any due date"), "Upcoming", "Overdue", "No date"] },
  );
  if (k === "tickets" && (evidenceState || [...evidenceByTicket.values()].some(evidence => evidence.state !== "No evidence linked"))) {
    filters.push({ label: "Evidence", value: evidenceState, change: setEvidenceState, data: [all("Any evidence"), ...evidenceStates] });
  }
  if (k === "activity") {
    const { actors, actions, kinds } = activity.facets;
    filters.push(
      { label: "Actor", value: actor, change: setActor, data: [all("All actors"), ...actors] },
      { label: "Action", value: action, change: setAction, data: [all("All actions"), ...actions] },
      { label: "Record type", value: type, change: setType, data: [all("All record types"), ...kinds.map((value) => ({ value, label: names[value] }))] },
      { label: "Date", value: period, change: setPeriod, data: [all("Any date"),
        { value: "0", label: "Today" }, { value: "-6", label: "Last 7 days" }, { value: "-29", label: "Last 30 days" }] },
    );
  }
  const grouping = k === "documents" ? documentGroup : k === "runs" ? runGroup : board ? boardGroup : ticketGroup;
  const groupingChoices = k === "documents" ? ["Family", "Type", "Project", "None"] :
    k === "runs" ? ["Day", "Agent", "Status", "None"] : board ? ["Status", "Milestone", "Type"] : ["Milestone", "Status", "Type", "None"];
  const showDisplay = k === "tickets" || k === "runs";
  const changeGrouping = (choice: string) => {
    if (k === "runs") setRunGroup(choice as RunGrouping);
    else if (board) setBoardGroup(choice as TicketGrouping);
    else setTicketGroup(choice as TicketGrouping);
  };
  const toggleGroup = (key: string) => setCollapsed((previous) => {
    const next = new Set(previous);
    if (next.has(key)) next.delete(key); else next.add(key);
    return next;
  });
  const open = (row: Row) => { if (k !== "activity") edit({ kind: k, row }); };
  const name = (row: Row, label = row.name) => <button className="plain" onClick={(event) => {event.stopPropagation(); open(row);}}>{label}</button>;

  const ticketGroups = new Map<string, { key: string; label?: string; rows: Row[] }>();
  if (k === "tickets") {
    if (board && grouping === "Status") statuses.forEach((label) => ticketGroups.set(label, { key: label, label, rows: [] }));
    for (const row of rows) {
      const key = grouping === "Milestone" ? row.milestone || "" : grouping === "Status" ? row.status || "" : grouping === "Type" ? workType(row) : "";
      const label = grouping === "Milestone" ? nameOf(db, "milestones", row.milestone) : grouping === "None" ? undefined : key;
      const group = ticketGroups.get(key) || { key, label, rows: [] };
      group.rows.push(row);
      ticketGroups.set(key, group);
    }
  }

  function list() {
    if (k === "activity") return <ActivityPageContents page={activity}><ActivityTimeline changes={activity.items} inspect={inspect} /></ActivityPageContents>;
    if (k === "runs") return <RunList db={db} rows={rows} grouping={runGroup} edit={edit} />;
    if (k === "documents")
      return <DocumentLibrary refresh={refresh} initialId={documentId} db={db} rows={rows} grouping={documentGroup} audit={audit} edit={edit} />;
    if (k === "roles" || k === "milestones") return <Directory kind={k} db={db} rows={rows} edit={edit} milestone={milestone} refresh={refresh}/>;
    if (!rows.length && !board) return <Empty>No matching records.</Empty>;
    if (k === "tickets") {
      const groups = [...ticketGroups.values()].map((group) => ({ ...group, key: layout + ":" + grouping + ":" + group.key }));
      if (board) {
        const occupied = groups.filter(group => group.rows.length);
        const empty = groups.filter(group => !group.rows.length);
        const statusLanes = grouping === "Status" && !mil;
        const renderLane = (group: typeof groups[number]) => {
          const isDone = statusLanes && group.label === "Done";
          const laneRows = isDone ? [...group.rows].sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || "")) : group.rows;
          const shown = isDone && !doneAll ? laneRows.slice(0, DONE_LIMIT) : laneRows;
          const collapsedEmpty = statusLanes && !group.rows.length;
          return <section className={"lane" + (collapsedEmpty ? " is-empty" : "")} key={group.key} data-drop={dropTarget===group.label || undefined}
          aria-label={collapsedEmpty ? `${group.label}: no tickets. Drop a ticket here to move it to ${group.label}.` : undefined}
          onDragOver={event=>{if(grouping!=="Status"||!dragging.current)return;event.preventDefault();event.dataTransfer.dropEffect="move";setDropTarget(group.label||"");}}
          onDragLeave={event=>{if(!event.currentTarget.contains(event.relatedTarget as Node))setDropTarget("");}}
          onDrop={event=>{event.preventDefault();const ticket=tickets.find(t=>t.id===dragging.current);if(ticket&&grouping==="Status"&&group.label)void moveTicket(ticket,group.label);dragging.current="";setDropTarget("");}}>
          {collapsedEmpty ? <div className="empty-lane-drop"><h2>{group.label}</h2><small>0</small><span aria-hidden="true">Drop here</span></div> : mil && !group.rows.length ? <h2 className="empty-lane-title">{group.label}<small>0 tickets</small></h2> : <>
          <h2><button className="row-group-label" aria-expanded={!collapsed.has(group.key)} onClick={()=>toggleGroup(group.key)}>{group.label}<small>{group.rows.length}</small></button></h2>
          {!collapsed.has(group.key)&&group.rows.length>0&&<div className="lane-tickets">{shown.map(row=><article className="tile" data-ticket={row.id} key={row.id} draggable={!moving && !operations.locked([projectResource(row.project || scope)])}
            onDragStart={event=>{const target=event.target as HTMLElement;if(target.closest("select,input,a,button:not([data-drag-title])")){event.preventDefault();return;}dragging.current=row.id;event.dataTransfer.setData("text/plain",row.id);event.dataTransfer.effectAllowed="move";}}
            onDragEnd={()=>{dragging.current="";setDropTarget("");}} onClick={event=>{if(!(event.target as HTMLElement).closest("button,select,input,a,label,summary"))open(row);}}>
            <TicketSummary db={db} ticket={row} open={open} metadata="role"/>{row.due&&<small>{dateLabel(row)}</small>}{needsAttention&&<Tag value={attention.get(row.id)||row.status||"Unspecified"}/>}
            <TicketEvidence evidence={evidenceByTicket.get(row.id)} />
            <TicketMenu row={row} moving={moving===row.id} locked={!!moving || operations.locked([projectResource(row.project || scope)])} onMove={next=>void moveTicket(row,next)} onOpen={()=>open(row)} />
          </article>)}
          {isDone && laneRows.length > DONE_LIMIT && <button type="button" className="lane-more" aria-expanded={doneAll} onClick={()=>setDoneAll(v=>!v)}>{doneAll ? "Show recent 6" : `Show all ${laneRows.length}`}</button>}
          </div>}
          {!collapsed.has(group.key)&&!group.rows.length&&<Empty>No tickets.</Empty>}
          </>}
        </section>;
        };
        if (!mil) return <>
          {grouping === "Status" && <StatusStrip counts={statusCountsOf(ticketCohort)} active={status} onPick={value=>setStatus(status===value?"":value)} />}
          <div className={"board" + (statusLanes ? " status-board" : "")} style={statusLanes ? { gridTemplateColumns: groups.map(g => g.rows.length ? "minmax(232px,1fr)" : "96px").join(" ") } : undefined}>{groups.map(renderLane)}</div>
        </>;
        return <>
          {occupied.length ? <div className="board milestone-board" data-lanes={occupied.length}>{occupied.map(renderLane)}</div> : <Empty>No matching tickets.</Empty>}
          {!!empty.length && <div className="board milestone-empty-lanes" aria-label="Empty status lanes">{empty.map(renderLane)}</div>}
        </>;
      }
      return <RecordTable headers={["Ticket", "Status", ...(grouping === "Milestone" ? [] : ["Milestone"]), "Role", "Due date", ...(audit ? ["Created", "Last edit"] : [])]}
        groups={groups.map((group) => ({ ...group, summary: group.label && <small className="group-progress">
          <span className="group-meter" aria-hidden="true"><i style={{width: percent(group.rows) + "%"}} /></span>{done(group.rows)}/{group.rows.length} done
        </small> }))}
        collapse={collapsed} toggle={toggleGroup} onOpen={open} makeCells={(row) => [
          <><TicketSummary db={db} ticket={row} open={open} metadata="none"/><TicketEvidence evidence={evidenceByTicket.get(row.id)} /></>,
          <><Tag value={row.status || "Unspecified"} />{needsAttention && attention.get(row.id) !== row.status && <small><Tag value={attention.get(row.id) || "Unspecified"} /></small>}</>,
          ...(grouping === "Milestone" ? [] : [nameOf(db, "milestones", row.milestone)]),
          nameOf(db, "roles", row.role), dueSoon(row) ? <Tag value={dateLabel(row)} /> : shortDate(row.due),
          ...(audit ? [stamp(row.created_at), <>{stamp(row.updated_at)}<small>{latestEditor(row)}</small></>] : []),
        ]} />;
    }
    return <RecordTable headers={["Project","Milestones","Tickets","Completion"]} groups={[{key:"",rows}]} onOpen={open} makeCells={row=>{const related=db.tickets.filter(t=>t.project===row.id);return [name(row),db.milestones.filter(m=>m.project===row.id).length,related.length,related.length?percent(related)+"%":"Progress pending"];}}/>;
  }
  const activeFilters = filters.filter(({value}) => value);
  const showMargin = k === "tickets" && (!mil || !!selectedMilestone) && !board && !needsAttention && due !== "Overdue";
  const scopedAttention = ticketCohort.filter(row => attention.has(row.id));
  return <>
    {k === "tickets" && <header className="heading">
      <div>
        <h1>{selectedMilestone?.name || "Tickets"}</h1>
        <p role="status">
          {rows.length === ticketCohort.length ? `${rows.length} ${rows.length === 1 ? "ticket" : "tickets"}` : `${rows.length} of ${ticketCohort.length} tickets shown`}
          {selectedMilestone ? ` · ${done(ticketCohort)} done in this milestone` : ` · ${scope ? nameOf(db, "projects", scope) : "All projects"}`}
        </p>
      </div>
      <Button size="sm" className="mast-action" leftSection={<Icon page="plus" />} onClick={onNewTicket}>New ticket</Button>
    </header>}
    {k === "tickets" && mil && !selectedMilestone && <Alert color="yellow" role="status" mb="md">This milestone is not available in the selected project. <button className="link" onClick={() => onMilestoneFilter("")}>View all project tickets</button></Alert>}
    <p className="sr-only" role="status" aria-live="polite">{announcement}</p>
    {moveFailure && <Alert color="red" role="alert" mb="md">Move failed: {moveFailure.message} <button className="link" onClick={()=>void moveTicket(moveFailure.row,moveFailure.status,true)}>Retry move</button> <button className="link" onClick={()=>void refresh?.()}>Reload records</button></Alert>}
    <div className="work-tools">
      <div className="work-modes" role="group" aria-label={monitoring ? "Record views" : "Layout"}>
        {monitoring && (["runs", "activity"] as const).map((page) => <button key={page} className="work-mode" aria-pressed={k === page} onClick={() => showMonitoring(page)}><Icon page={page} />{page === "runs" ? "Agent runs" : "Activity log"}</button>)}
        {k === "tickets" && ["Board", "List"].map((mode) => <button key={mode} className="work-mode" aria-pressed={layout === mode} onClick={() => setLayout(mode)}><Icon page={mode === "List" ? "list" : "board"} />{mode}</button>)}
      </div>
      <div className="work-utilities">
        <TextInput type="search" variant="unstyled" size="sm" aria-label={"Search " + (k === "activity" ? "changes" : names[k].toLowerCase())}
          placeholder={"Search " + (k === "activity" ? "changes" : names[k].toLowerCase()) + "…"} value={query} onChange={(event) => search(event.currentTarget.value)}
          leftSection={<Icon page="search" />} className="record-search" />
        {filters.length > 0 && <Popover position="bottom-end" shadow="sm" withinPortal>
          <Popover.Target><button className="utility"><Icon page="filters" />Filters</button></Popover.Target>
          <Popover.Dropdown><div className="filter-fields">{filters.map(({label, value, change, data}) =>
            <NativeSelect key={label} size="xs" label={label} value={value} onChange={(event) => change(event.currentTarget.value)} data={data} />,
          )}</div></Popover.Dropdown>
        </Popover>}
        {showDisplay && <Menu position="bottom-end" shadow="sm">
          <Menu.Target><button className="utility"><Icon page="columns" />Display</button></Menu.Target>
          <Menu.Dropdown><Menu.Label>Group by</Menu.Label>
            {groupingChoices.map((choice) => <Menu.Item key={choice} aria-label={choice === grouping ? choice + " (selected)" : choice}
              leftSection={<span aria-hidden="true">{choice === grouping ? "●" : "○"}</span>} onClick={() => changeGrouping(choice)}>{choice}</Menu.Item>)}
            {k !== "runs" && !board && <><Menu.Divider /><Menu.Item onClick={() => showAudit(!audit)}>
              {audit ? "Hide edit metadata" : "Show edit metadata"}</Menu.Item></>}
          </Menu.Dropdown>
        </Menu>}
      </div>
    </div>
    {activeFilters.length > 0 && <div className="active-filters">{activeFilters.map(({ label, value, change, data }) => {
      const current = data.find((option) => (typeof option === "string" ? option : option.value) === value);
      const text = typeof current === "object" ? current.label : value;
      return <button key={label} className="filter-chip" onClick={() => change("")} aria-label={`Clear ${label}: ${text}`}>{label}: {text} ×</button>;
    })}</div>}
    <div className={showMargin ? "tickets-with-margin" : undefined}>
      <div className="work-list">{list()}
        {alerts.length > 0 && <section className="attention-project-runs"><h2>Project runs needing attention</h2><RunList db={db} rows={alerts} grouping="None" edit={edit} /></section>}
      </div>
      {showMargin && <section className="work-margin" aria-label={selectedMilestone ? "Milestone summary" : "Project summary"}>
        <h2>{selectedMilestone ? "Milestone completion" : "Project completion"}</h2><CompletionDial tickets={ticketCohort} compact />
        <h2>Needs attention</h2>
        {scopedAttention.map((row) => <button className="margin-note" key={row.id} onClick={() => open(row)}>
          <Tag value={attention.get(row.id)!} /><strong>{row.name}</strong><Icon page="arrow" />
        </button>)}
        {!scopedAttention.length && <Empty>Nothing needs attention.</Empty>}
      </section>}
    </div>
  </>;
}

const DONE_LIMIT = 6;
const statusCountsOf = (rows: Row[]) => Object.fromEntries(statuses.map(value => [value, rows.filter(row => row.status === value).length])) as Record<string, number>;

/** Counts by status; each segment filters the board, and selecting it again clears the filter. */
function StatusStrip({ counts, active, onPick }: { counts: Record<string, number>; active: string; onPick: (status: string) => void }) {
  const order = ["Done", "In progress", "Blocked", "Planned"].filter(value => statuses.includes(value));
  const total = order.reduce((sum, value) => sum + (counts[value] || 0), 0);
  if (!total) return null;
  return (
    <div className="status-strip" role="group" aria-label="Filter the board by status">
      <div className="status-strip__bar" aria-hidden="true">
        {order.filter(value => counts[value]).map(value => <span key={value} style={{ flexGrow: counts[value], background: statusFill[value as Status] }} data-dim={active && active !== value || undefined} />)}
      </div>
      <div className="status-strip__keys">
        {order.map(value => (
          <button key={value} type="button" aria-pressed={active === value} disabled={!counts[value] && active !== value} onClick={() => onPick(value)}>
            <span className="cv-key-dot" style={{ background: statusFill[value as Status] }} /><span aria-hidden="true">{statusShape[value as Status]}</span>{value}<b>{counts[value] || 0}</b>
          </button>
        ))}
        {active && <button type="button" className="link status-strip__clear" onClick={() => onPick(active)}>Clear filter</button>}
      </div>
    </div>
  );
}

/** Card actions live in one menu; dragging stays on the card itself. */
function TicketMenu({ row, moving, locked, onMove, onOpen }: { row: Row; moving: boolean; locked: boolean; onMove: (status: string) => void; onOpen: () => void }) {
  const [copied, setCopied] = useState(false);
  const link = `${location.origin}${location.pathname}#project/${encodeURIComponent(row.project || "")}/tickets/${encodeURIComponent(row.id)}`;
  return (
    <div className="ticket-actions">
      {moving && <small role="status">Moving…</small>}
      {copied && <small role="status">Link copied</small>}
      <Menu position="bottom-end" shadow="sm" withinPortal>
        <Menu.Target><button type="button" className="ticket-menu" aria-label={`Actions for ${row.name}`}>⋯</button></Menu.Target>
        <Menu.Dropdown>
          <Menu.Label>Move to</Menu.Label>
          {statuses.filter(value => value !== row.status).map(value => <Menu.Item key={value} disabled={locked} onClick={() => onMove(value)}>
            <span aria-hidden="true">{statusShape[value as Status]} </span>{value}</Menu.Item>)}
          <Menu.Divider />
          <Menu.Item onClick={onOpen}>Open</Menu.Item>
          <Menu.Item onClick={() => { void navigator.clipboard?.writeText(link).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); }); }}>Copy link</Menu.Item>
        </Menu.Dropdown>
      </Menu>
    </div>
  );
}
