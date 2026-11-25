import { flushSync } from "react-dom";
import { mutateRecord } from "./features/operations/record-mutation";
import { useOperations } from "./features/operations/Operations";
import { OperationFeedback } from "./features/operations/Operations";
import { operations, inFlight } from "./features/operations/operation-store";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import {
  Alert,
  Button,
  Drawer,
  Group,
  Loader,
} from "@mantine/core";
import { useFocusTrap, useMediaQuery } from "@mantine/hooks";
import { CanvasWorkspace, DesignCanvas } from "./DesignCanvas";
import { Dashboard } from "./Dashboard";
import { Assistant } from "./Assistant";
import { Empty, History, Icon } from "./Common";
import { Guide } from "./Guide";
import { Listing } from "./Listing";
import { Projects } from "./Projects";
import { InfoHelp } from "./features/help/InfoHelp";
import { RecordEditor } from "./RecordEditor";
import {
  type Page,
  type Change,
  type Workspace,
  type Editor,
  type Kind,
  type TicketView,
  kinds,
  names,
  single,
  done,
  nameOf,
  percent,
  request,
  errorText,
  scoped,
} from "./model";

const navigation = [
  { label: "Workspace", pages: ["projects"] },
  { label: "Project", pages: ["dashboard", "documents", "canvas", "tickets", "milestones"] },
  { label: "Operations", pages: ["roles", "runs"] },
] as const;

function routeParts(route = location.hash): string[] {
  return route.replace(/^#/, "").split("?", 1)[0].split("/");
}
function assistantRunFromURL(route = location.hash): string {
  const query = route.split("?", 2)[1] || "";
  return new URLSearchParams(query).get("run") || "";
}
function pageFromURL(route = location.hash): Page {
  const parts = routeParts(route);
  const slug = parts[0] === "project" ? parts[2] : parts[0];
  if (slug === "reviews") return "activity"; // Legacy links lead to the existing log.
  return Object.prototype.hasOwnProperty.call(names, slug)
    ? (slug as Page)
    : "dashboard";
}
function projectFromURL(route = location.hash): string {
  const parts = routeParts(route);
  if (parts[0] !== "project") return "";
  try {
    return decodeURIComponent(parts[1] || "");
  } catch {
    return "";
  }
}
function recordIdFromURL(route: string, page: Page): string {
  const parts = routeParts(route);
  if (parts[0] === "project") {
    const recordId = parts[3] || "";
    return page === "tickets" && ["attention", "overdue"].includes(recordId) ? "" : recordId;
  }
  if (page === "tickets" && ["attention", "overdue"].includes(parts[1])) return "";
  return parts[1] || "";
}
function ticketViewFromURL(route = location.hash): TicketView {
  const parts = routeParts(route);
  const segment = parts[0] === "project" ? parts[3] : parts[1];
  if (pageFromURL(route) !== "tickets") return "";
  if (segment === "attention") return "attention";
  if (segment === "overdue") return "overdue";
  return "";
}
export default function App() {
  const [db, setDB] = useState<Workspace | null>(null),
    [error, setError] = useState(""),
    [page, setPage] = useState(pageFromURL),
    [ticketView, setTicketView] = useState(ticketViewFromURL),
    [scope, setScope] = useState(() => projectFromURL()),
    [mil, setMil] = useState("");
  const scopeRef = useRef(scope);
  useEffect(() => { scopeRef.current = scope; }, [scope]);
  const [editor, setEditor] = useState<Editor | null>(null),
    [entry, setEntry] = useState<Change | null>(null),
    [trash, setTrash] = useState(false),
    [trashError, setTrashError] = useState(""),
    [busy, setBusy] = useState("");
  const [guide, showGuide] = useState(false),
    [mobileOpen, setMobileOpen] = useState(false),
    [routeMessage, setRouteMessage] = useState("");
  const guideButton = useRef<HTMLButtonElement>(null);
  const mobileMenuButton = useRef<HTMLButtonElement>(null);
  const isNarrow = useMediaQuery("(max-width: 900px)") || false;
  const mobileFocusTrapRef = useFocusTrap(mobileOpen && isNarrow && !guide);
  const sidebarRef = useCallback((element: HTMLElement | null) => {
    mobileFocusTrapRef(element);
    if (element) element.inert = !!isNarrow && !mobileOpen;
  }, [isNarrow, mobileFocusTrapRef, mobileOpen]);
  const [route, setRoute] = useState(location.hash);
  const openedRoute = useRef(""),
    handledInvalidRoute = useRef("");
  const mobileWasOpen = useRef(mobileOpen);
  useEffect(() => {
    const wasOpen = mobileWasOpen.current;
    mobileWasOpen.current = mobileOpen;
    if (wasOpen && !mobileOpen && isNarrow && !guide) {
      window.requestAnimationFrame(() => mobileMenuButton.current?.focus());
    }
  }, [mobileOpen, isNarrow]);
  useEffect(() => {
    if (!mobileOpen || !isNarrow || guide) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      event.stopPropagation();
      setMobileOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen, isNarrow, guide]);
  useEffect(() => {
    if (!mobileOpen || !isNarrow) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previousOverflow; };
  }, [mobileOpen, isNarrow]);
  const id = recordIdFromURL(route, page);
  useEffect(() => { document.title = names[page] + ' · AgentBoard'; }, [page]);
  const recordRoute = id && id !== "attention" && id !== "overdue" && kinds.includes(page as Kind);
  const target = db && recordRoute ? db[page as Kind].find(row => row.id === id) : undefined;
  const requestedProject = projectFromURL(route);
  const targetMismatch = !!requestedProject && !!target?.project && target.project !== requestedProject;
  const routeTarget = targetMismatch ? undefined : target;
  const routeScope = page === "projects"
    ? ""
    : requestedProject || (recordRoute ? routeTarget?.project || "" : "") || scope;
  const activeProject = db?.projects.find(project => project.id === routeScope);
  const selectedProjectId = activeProject?.id || routeScope;
  const viewerProfile = page === "canvas" && id
    ? db?.documents.find(document => document.id === id && document.canvas_versions?.length)
    : undefined;
  useEffect(() => {
    if (!routeTarget || openedRoute.current === route) return;
    openedRoute.current = route;
    setScope(routeTarget.project || (page === "projects" ? "" : routeTarget.id));
    if (page !== "documents") setEditor({ kind: page as Kind, row: routeTarget });
  }, [routeTarget, route, page]);
  const operationList = useOperations();
  useEffect(() => {
    if (!operations.pending) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [operationList]);
  const seq = useRef(0),
    activeURL = useRef(location.href);
  const backgroundRead = useRef(false);
  const loadWorkspace = useCallback(async (strict: boolean, verify?: (data: Workspace) => boolean) => {
    if (!strict && (operations.getSnapshot().some(inFlight) || backgroundRead.current)) return;
    if (!strict) backgroundRead.current=true;
    const token = ++seq.current, epoch = operations.epoch;
    try {
      const data = await request<Workspace>("workspace");
      if (epoch !== operations.epoch || token !== seq.current) {
        if (strict) throw new Error("A newer operation changed the workspace. Retry sync.");
        return;
      }
      if (verify && !verify(data)) throw new Error("The latest response does not confirm this change yet. Retry sync.");
      // A protected action releases its lock only after React has committed this snapshot.
      if(strict)flushSync(()=>{setDB(data);setError("");});
      else {setDB(data);setError("");}
    } catch (e) {
      if (strict) throw e;
      if (token === seq.current && epoch === operations.epoch) setError(errorText(e));
    } finally {
      if (!strict) backgroundRead.current=false;
    }
  }, []);
  const refresh = useCallback(() => loadWorkspace(false), [loadWorkspace]);
  const syncWorkspace = useCallback((verify?: (data: Workspace) => boolean) => loadWorkspace(true, verify), [loadWorkspace]);
  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, 5000);
    window.addEventListener("focus", refresh);
    const back = () => {
      if (activeURL.current === location.href) return;
      if (
        !window.dispatchEvent(
          new Event("agentboard:before-navigate", { cancelable: true }),
        )
      ) {
        history.pushState({}, "", activeURL.current);
        return;
      }
      activeURL.current = location.href;
      openedRoute.current = "";
      handledInvalidRoute.current = "";
      setRoute(location.hash);
      setPage(pageFromURL());
      setTicketView(ticketViewFromURL());
      const destinationPage = pageFromURL(location.hash);
      const destinationScope = destinationPage === "projects" ? "" : projectFromURL() || scopeRef.current;
      setScope(destinationScope);
      scopeRef.current = destinationScope;
      setMobileOpen(false);
      setRouteMessage("");
      setMil("");
      setEditor(null);
      setTrash(false);
      setEntry(null);
    };
    window.addEventListener("popstate", back);
    window.addEventListener("hashchange", back);
    return () => {
      ++seq.current;
      window.clearInterval(timer);
      window.removeEventListener("focus", refresh);
      window.removeEventListener("popstate", back);
      window.removeEventListener("hashchange", back);
    };
  }, [refresh]);
  useEffect(() => {
    if (!db) return;
    const resolvedProject = requestedProject || routeTarget?.project || (routeTarget?.id && page === "projects" ? routeTarget.id : "") || activeProject?.id || (page === "projects" ? "" : scope);
    const invalidProject = !!resolvedProject && !db.projects.some(project => project.id === resolvedProject);
    const missingContext = page !== "projects" && !resolvedProject && !viewerProfile;
    if (!invalidProject && !missingContext) {
      handledInvalidRoute.current = "";
      return;
    }
    if (handledInvalidRoute.current === route) return;
    handledInvalidRoute.current = route;
    setRouteMessage(invalidProject
      ? "That project is no longer available. Choose another project."
      : recordRoute
        ? "That record is no longer available. Choose a project to continue."
        : "Choose a project before opening its workspace.");
    if (!window.dispatchEvent(new Event("agentboard:before-navigate", { cancelable: true }))) return;
    openedRoute.current = "";
    setEditor(null);
    setScope("");
    setTicketView("");
    setMil("");
    setPage("projects");
    setRoute("#projects");
    activeURL.current = location.origin + location.pathname + location.search + "#projects";
    history.replaceState({}, "", "#projects");
  }, [db, page, recordRoute, requestedProject, scope, routeTarget, viewerProfile, route, activeProject]);
  function go(p: Page, nextView: TicketView = "", milestoneId = "", skipGuard = false) {
    const nextScope = p === "projects" ? "" : selectedProjectId;
    if (p !== "projects" && !nextScope) {
      go("projects", "", "", skipGuard);
      setRouteMessage("Choose a project before opening its workspace.");
      return;
    }
    if (!skipGuard && !window.dispatchEvent(new Event("agentboard:before-navigate", { cancelable: true }))) return;
    setPage(p);
    setTicketView(nextView);
    setScope(nextScope);
    scopeRef.current = nextScope;
    setMil(milestoneId);
    const hash = p === "projects"
      ? "#projects"
      : `#project/${encodeURIComponent(nextScope)}/${p}` + (p === "tickets" && nextView ? "/" + nextView : "");
    openedRoute.current = "";
    handledInvalidRoute.current = "";
    setRoute(hash);
    if (location.hash !== hash) history.pushState({}, "", hash);
    activeURL.current = location.href;
    setMobileOpen(false);
    setRouteMessage("");
    setEditor(null);
    setEntry(null);
    setTrash(false);
    if (p !== page) window.scrollTo(0, 0);
  }
  function openProject(projectId: string) {
    if (!window.dispatchEvent(new Event("agentboard:before-navigate", { cancelable: true }))) return;
    const hash = `#project/${encodeURIComponent(projectId)}/dashboard`;
    setPage("dashboard");
    setTicketView("");
    setScope(projectId);
    scopeRef.current = projectId;
    setMil("");
    openedRoute.current = "";
    handledInvalidRoute.current = "";
    setRoute(hash);
    if (location.hash !== hash) history.pushState({}, "", hash);
    activeURL.current = location.href;
    setMobileOpen(false);
    setRouteMessage("");
    setEditor(null);
    setEntry(null);
    setTrash(false);
    window.scrollTo(0, 0);
  }
  function openAssistantRun(runId: string) {
    if (!selectedProjectId) {
      go("projects");
      return;
    }
    if (!window.dispatchEvent(new Event("agentboard:before-navigate", { cancelable: true }))) return;
    const hash = `#project/${encodeURIComponent(selectedProjectId)}/assistant?run=${encodeURIComponent(runId)}`;
    setPage("assistant");
    setTicketView("");
    setScope(selectedProjectId);
    scopeRef.current = selectedProjectId;
    openedRoute.current = "";
    handledInvalidRoute.current = "";
    setRoute(hash);
    if (location.hash !== hash) history.pushState({}, "", hash);
    activeURL.current = location.href;
    setMobileOpen(false);
    setRouteMessage("");
    setEditor(null);
    setEntry(null);
    setTrash(false);
    setMil("");
  }
  function openAssistantTicket(ticketId: string) {
    const ticket = db?.tickets.find((item) => item.id === ticketId);
    if (!ticket) {
      setRouteMessage("This linked ticket is no longer available.");
      return;
    }
    if (!window.dispatchEvent(new Event("agentboard:before-navigate", { cancelable: true }))) return;
    const project = ticket.project || selectedProjectId;
    const hash = `#project/${encodeURIComponent(project)}/tickets/${encodeURIComponent(ticket.id)}`;
    setPage("tickets");
    setTicketView("");
    setScope(project);
    scopeRef.current = project;
    openedRoute.current = "";
    handledInvalidRoute.current = "";
    setRoute(hash);
    if (location.hash !== hash) history.pushState({}, "", hash);
    activeURL.current = location.href;
    setMobileOpen(false);
    setRouteMessage("");
    setEditor(null);
    setEntry(null);
    setTrash(false);
    setMil("");
  }
  const milestone = (id: string) => go("tickets", "", id);
  const createKind: Kind =
    page === "dashboard"
      ? db && !db.projects.length
        ? "projects"
        : "tickets"
      : page === "canvas" ? "documents" : page === "activity"
        ? "projects" : page === "assistant" ? "tickets"
        : page;
  const newRecord = () => setEditor({ kind: createKind });
  const monitoring = page === "runs" || page === "activity";
  const section = monitoring ? "Runs & activity" : names[page];
  const navPage = monitoring ? "runs" : page;
  const projectTickets = scoped(db?.tickets || [], selectedProjectId, "tickets");
  const blockedTickets = projectTickets.filter(ticket => ticket.status === "Blocked").length;
  const dashboardSubtitle = [
    activeProject?.description,
    projectTickets.length ? `${done(projectTickets)} of ${projectTickets.length} tickets done` : "Progress pending",
    blockedTickets ? `${blockedTickets} blocked` : "",
  ].filter(Boolean).join(" · ");
  function closeGuide() {
    showGuide(false);
    const narrow = window.matchMedia("(max-width: 900px)").matches;
    if (narrow) setMobileOpen(true);
    window.setTimeout(() => guideButton.current?.focus(), 220);
  }
  async function restore(k: Kind, id: string, revision: number) {
    setBusy(id);
    setTrashError("");
    try {
      const row = db?.trash.find(item => item.k === k && item.r.id === id)?.r;
      if (!row) return;
      await mutateRecord({kind:k,project:row.project || row.id,row,action:"restore",refresh:syncWorkspace,
        write:()=>request(k + "/" + encodeURIComponent(id) + "/restore", "POST", { revision })});
    } catch (e) {
      setTrashError(errorText(e));
    } finally {
      setBusy("");
    }
  }
  const trashList =
    db?.trash.filter(
      ({ k, r }) => !selectedProjectId || (k === "projects" ? r.id : r.project) === selectedProjectId,
    ) || [];
  if (page === "canvas" && id) {
    if (!db) return <div className="canvas-viewer-message">{error || "Loading canvas…"}</div>;
    const profile = viewerProfile;
    return profile ? <DesignCanvas key={profile.id + "/" + (route.split("/")[2] || "")} document={profile} viewer /> :
      <div className="canvas-viewer-message"><p>This canvas is unavailable.</p><a href="#canvas">Back to canvases</a></div>;
  }
  return (
    <div className="shell">
      <a className="skip-content" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById("main-content")?.focus(); }}>Skip to content</a>
      <div className="mobilebar" aria-hidden={isNarrow && mobileOpen}>
        <button
          ref={mobileMenuButton}
          type="button"
          className="mobile-menu"
          aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileOpen}
          aria-controls="workspace-navigation"
          onClick={() => setMobileOpen((open) => !open)}
        >
          <Icon page="list" />
        </button>
        <span className="mobilebar-context">
          {activeProject ? <><b>{activeProject.name}</b><span aria-hidden="true"> / </span></> : null}
          <span>{section}</span>
        </span>
      </div>
      {mobileOpen && <button type="button" className="sidebar-scrim" aria-label="Close navigation menu" onClick={() => setMobileOpen(false)} />}
      <aside
        id="workspace-navigation"
        ref={sidebarRef}
        className={`sidebar${mobileOpen ? " is-open" : ""}`}
        aria-hidden={isNarrow && !mobileOpen}
        role={isNarrow && mobileOpen ? "dialog" : undefined}
        aria-modal={isNarrow && mobileOpen ? true : undefined}
        aria-label={isNarrow && mobileOpen ? "Workspace navigation" : undefined}
      >
        <div className="brand">
          <span className="brand-fold" aria-hidden="true"><i /><i /><i /></span>AgentBoard
          <button className="sidebar-close" type="button" aria-label="Close navigation menu" onClick={() => setMobileOpen(false)}>
            <span aria-hidden="true">×</span>
          </button>
        </div>
        <div className="project-context" data-empty={!activeProject || undefined}>
          {activeProject ? <>
            <small>Current project</small>
            <b className="project-context-name" title={activeProject.name}>{activeProject.name}</b>
            <span className="project-context-line">
              {scoped(db?.tickets || [], selectedProjectId, "tickets").length
                ? `${percent(scoped(db?.tickets || [], selectedProjectId, "tickets"))}% complete`
                : "Progress pending"}
              {db && scoped(db.tickets, selectedProjectId, "tickets").some(ticket => ticket.status === "Blocked") && (
                <span className="warn"> · {scoped(db.tickets, selectedProjectId, "tickets").filter(ticket => ticket.status === "Blocked").length} blocked</span>
              )}
            </span>
            <span className={`project-context-bar${db && scoped(db.tickets, selectedProjectId, "tickets").length ? "" : " is-empty"}`} aria-hidden="true">
              <i style={{ width: `${percent(scoped(db?.tickets || [], selectedProjectId, "tickets"))}%` }} />
            </span>
            <button className="link" onClick={() => go("projects")}>Switch project <Icon page="arrow" /></button>
          </> : <>
            <div className="with-info"><small>No project selected</small><InfoHelp label="project navigation">Choose a project to open its dashboard, documents, Canvas and work.</InfoHelp></div>
          </>}
        </div>
        <nav aria-label="Workspace">
          {navigation.map(({ label, pages }) => (
            <Fragment key={label}>
              <small>{label}</small>
              {pages.map((k) => (
                <button
                  key={k}
                  className={navPage === k ? "active" : ""}
                  aria-current={navPage === k ? "page" : undefined}
                  disabled={k !== "projects" && !selectedProjectId}
                  onClick={() => go(k)}
                >
                  <Icon page={k === "canvas" ? "Design" : k} />
                  {k === "runs" ? "Runs & activity" : names[k]}
                </button>
              ))}
            </Fragment>
          ))}
          <button
            className={page === "assistant" ? "active" : ""}
            aria-current={page === "assistant" ? "page" : undefined}
            disabled={!selectedProjectId}
            onClick={() => go("assistant")}
          ><Icon page="runs" />InApp Assistant</button>
          <button ref={guideButton} className={guide ? "active" : ""} aria-current={guide ? "page" : undefined} onClick={() => { setMobileOpen(false); showGuide(true); }}><Icon page="file" />AgentBuild guide</button>
        </nav>
      </aside>
      <main id="main-content" tabIndex={-1} aria-label={section} aria-hidden={isNarrow && mobileOpen}>
        <header className="topbar">
          <ol className="breadcrumb" aria-label="Breadcrumb">
            <li><button onClick={() => go("projects")}>Workspace</button></li>
            {activeProject && <li><span title={activeProject.name}>{activeProject.name}</span></li>}
            <li aria-current="page"><strong>{section}</strong></li>
          </ol>
        </header>
        <div id="page">
          {page !== "canvas" && page !== "projects" && page !== "assistant" && page !== "dashboard" && <div className="heading">
            <div>
              <h1>{monitoring ? <>Runs <em>&amp;</em> activity</> : section}</h1>
              <p>
                {db
                    ? page === "activity"
                      ? db.activity.filter((l) => !selectedProjectId || l.project === selectedProjectId).length + " changes"
                      : page === "runs"
                        ? scoped(db.runs, selectedProjectId, "runs").length + " runs / " + scoped(db.runs, selectedProjectId, "runs").filter((run) => run.status === "Running").length + " running"
                        : scoped(db[page as Kind], selectedProjectId, page as Kind).length + " " + names[page].toLowerCase() + " · " + (selectedProjectId ? nameOf(db, "projects", selectedProjectId) : "All projects")
                    : ""}
              </p>
            </div>
          {db &&
              (page === "activity" ? (
                <Button
                  size="sm"
                  variant="default"
                  className="mast-action"
                  leftSection={<Icon page="trash" />}
                  onClick={() => {
                    setTrashError("");
                    setTrash(true);
                  }}
                >
                  Deleted records
                </Button>
              ) : (
                <Button size="sm" className="mast-action" leftSection={<Icon page="plus" />} onClick={newRecord}>
                  {page === "runs"
                    ? "Report run"
                    : "New " + single[createKind]}
                </Button>
              ))}
          </div>}
          {routeMessage && <Alert color="yellow" role="status" mb="md">{routeMessage}</Alert>}
          {db && recordRoute && !routeTarget && <Alert color="yellow" role="alert">
            {targetMismatch ? "This record does not belong to the selected project." : "This record is unavailable. It may have been deleted or this link may be out of date."}{" "}
            <button className="link" onClick={() => go(page, "", "", true)}>Return to {section.toLowerCase()}</button>
          </Alert>}
          {!editor && <OperationFeedback />}
          {error && (
            <Alert color="red" role="alert" mb="md">
              {db ? "Refresh failed. Showing previously loaded data. " : "Workspace load failed. "}{error}{" "}
              <button className="link" onClick={refresh}>
                Retry
              </button>
            </Alert>
          )}
          {!db && !error && (
            <Group>
              <Loader size="sm" />
              <span>Loading workspace…</span>
            </Group>
          )}
          {db && ((!recordRoute || routeTarget) || page === "projects") &&
            (page === "projects" ? <Projects db={db} openProject={openProject} editProject={(row) => setEditor({ kind: "projects", row })} /> : page === "canvas" ? <CanvasWorkspace db={db} scope={selectedProjectId} /> : page === "assistant" ? (
              <Assistant
                key={selectedProjectId}
                projectId={selectedProjectId}
                projectName={activeProject?.name || "Selected project"}
                db={db}
                initialRunId={assistantRunFromURL(route) || undefined}
                onOpenRun={openAssistantRun}
                onCloseRun={() => go("assistant")}
                onShowRuns={() => go("runs")}
                onOpenTicket={openAssistantTicket}
                onShowTickets={() => go("tickets")}
                onRefreshWorkspace={syncWorkspace}
              />
            ) : page === "dashboard" ? (
              <Dashboard
                db={db}
                scope={selectedProjectId}
                go={go}
                milestone={milestone}
                guide={() => showGuide(true)}
              />
            ) : (
              <Listing
                refresh={syncWorkspace}
                documentId={page === "documents" ? routeTarget?.id : undefined}
                key={[page, selectedProjectId, mil, ticketView, routeTarget?.id].join(":")}
                db={db}
                page={page}
                scope={selectedProjectId}
                edit={setEditor}
                inspect={setEntry}
                initialMil={mil}
                initialTicketView={ticketView}
                showMonitoring={go}
                milestone={milestone}
              />
            ))}
        </div>
      </main>
      <Guide opened={guide} close={closeGuide} project={activeProject?.name} />
      {db && editor && (
        <RecordEditor
          key={[
            editor.kind,
            editor.row?.id,
            editor.row?.revision,
            editor.project,
            editor.panel,
          ].join(":")}
          db={db}
          editor={editor}
          scope={selectedProjectId}
          close={() => { setEditor(null); if (recordRoute && page !== "documents") go(page, "", "", true); }}
          open={setEditor}
          refresh={syncWorkspace}
        />
      )}
      <Drawer
        opened={!!entry}
        onClose={() => setEntry(null)}
        title="Change details"
        closeButtonProps={{ "aria-label": "Close change details" }}
        position="right"
        size="min(490px,95vw)"
      >
        {entry && (
          <>
            <h3 className="detail">{entry.name}</h3>
            <History entry={entry} db={db || undefined} />
          </>
        )}
      </Drawer>
      <Drawer
        opened={trash}
        onClose={() => setTrash(false)}
        title="Deleted records"
        closeButtonProps={{ "aria-label": "Close deleted records" }}
        position="right"
        size="min(490px,95vw)"
      >
        <OperationFeedback />
        {trashError && (
          <Alert role="alert" color="red">
            {trashError}
          </Alert>
        )}
        {trashList.map(({ k, r }) => (
          <div className="log spread" key={r.id}>
            <div>
              {r.name} <small>· {single[k]}</small>
            </div>
            <Button
              variant="light"
              size="xs"
              loading={busy === r.id}
              disabled={!!busy || operations.locked(["project:" + (r.project || r.id)])}
              onClick={() => restore(k, r.id, r.revision)}
            >
              Restore
            </Button>
          </div>
        ))}
        {!trashList.length && <Empty>No deleted records.</Empty>}
      </Drawer>
    </div>
  );
}
