import { flushSync } from "react-dom";
import { conditionalRead, type Snapshot } from "./features/workspace/conditional-read";
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
import { milestoneFromTicketRoute, withMilestoneTicketFilter } from "./features/tickets/milestone";
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
  workspacePath,
  errorText,
  scoped,
} from "./model";

const navigation = [
  { label: "Workspace", pages: ["projects"] },
  { label: "Project work", pages: ["dashboard", "documents", "canvas", "tickets", "milestones"] },
  { label: "Operations", pages: ["runs", "assistant"] },
  { label: "Project settings", pages: ["roles"] },
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
  const [view, setView] = useState<{ key: string; snapshot: Snapshot<Workspace> } | null>(null),
    [error, setError] = useState(""),
    [page, setPage] = useState(pageFromURL),
    [ticketView, setTicketView] = useState(ticketViewFromURL),
    [scope, setScope] = useState(() => projectFromURL());
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
  const requestedProject = projectFromURL(route);
  const canvasViewer = page === "canvas" && !!id;
  const bareKind = !requestedProject && page !== "projects" && recordRoute ? page as Kind : null;
  const readKey = canvasViewer ? `canvases/${encodeURIComponent(id)}/viewer`
    : page === "projects" ? workspacePath("")
    : requestedProject ? workspacePath(requestedProject)
    : bareKind ? `records/${bareKind}/${encodeURIComponent(id)}/project` : workspacePath(scope);
  const db = view?.key === readKey ? view.snapshot.data : null;
  const target = db && recordRoute ? db[page as Kind].find(row => row.id === id) : undefined;
  const targetMismatch = !!requestedProject && !!target?.project && target.project !== requestedProject;
  const routeTarget = targetMismatch ? undefined : target;
  const routeScope = page === "projects"
    ? ""
    : requestedProject || (recordRoute ? routeTarget?.project || "" : "") || scope;
  const activeProject = db?.projects.find(project => project.id === routeScope);
  const selectedProjectId = activeProject?.id || routeScope;
  const viewerProfile = canvasViewer
    ? db?.documents.find(document => document.id === id && document.canvas_versions?.length
      && (!requestedProject || document.project === requestedProject))
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
  const backgroundRead = useRef<{key: string; token: number} | null>(null);
  const appliedKey = useRef("");
  const snapshotRef = useRef<Snapshot<Workspace>>();
  const activeReadKey = useRef(readKey);
  activeReadKey.current = readKey;
  const resolution = useRef<{ key: string; path: string }>();
  const loadWorkspace = useCallback(async (strict: boolean, verify?: (data: Workspace) => boolean, verificationProject?: string) => {
    const key = activeReadKey.current;
    if (!strict && (operations.getSnapshot().some(inFlight) || backgroundRead.current?.key === key)) return;
    const token = ++seq.current, epoch = operations.epoch;
    if (!strict) backgroundRead.current = { key, token };
    const current = () => epoch === operations.epoch && token === seq.current && key === activeReadKey.current;
    try {
      let path = key;
      if (key.startsWith("records/")) {
        if (resolution.current?.key === key) path = resolution.current.path;
        else {
          try {
            const result = await request<{ project: string }>(key);
            path = workspacePath(result.project);
            if (current()) resolution.current = { key, path };
          } catch (error) {
            if ((error as {status?: number}).status !== 404) throw error;
            path = workspacePath("");
          }
        }
      }
      let snapshot: Snapshot<Workspace>;
      try { snapshot = await conditionalRead(path, snapshotRef.current); }
      catch (error) {
        if ((error as {status?: number}).status !== 404 || path === workspacePath("") || path.startsWith("canvases/")) throw error;
        // Load the directory so the existing missing-project and record recovery can run.
        snapshot = await conditionalRead(workspacePath(""), snapshotRef.current);
      }
      if (verify) {
        const verifyPath = verificationProject === undefined ? snapshot.path : workspacePath(verificationProject);
        const proof = verifyPath === snapshot.path ? snapshot : await conditionalRead<Workspace>(verifyPath);
        if (!verify(proof.data)) throw new Error("The latest response does not confirm this change yet. Retry sync.");
      }
      if (!current()) {
        if (strict) throw new Error("A newer operation changed the workspace. Retry sync.");
        return;
      }
      const commit = () => {
        if (appliedKey.current !== key || snapshotRef.current !== snapshot) {
          appliedKey.current = key;
          snapshotRef.current = snapshot;
          setView({ key, snapshot });
        }
        setError("");
      };
      if (strict) flushSync(commit); else commit();
    } catch (e) {
      if (strict) throw e;
      if (current()) {
        if (key.startsWith("canvases/") && (e as { status?: number }).status === 404) setView(null);
        setError(errorText(e));
      }
    } finally {
      if (!strict && backgroundRead.current?.token === token) backgroundRead.current = null;
    }
  }, []);
  const refresh = useCallback(() => loadWorkspace(false), [loadWorkspace]);
  const syncWorkspace = useCallback((verify?: (data: Workspace) => boolean, project?: string) =>
    loadWorkspace(true, verify, project), [loadWorkspace]);
  useEffect(() => { setError(""); void refresh(); }, [readKey, refresh]);
  useEffect(() => {
    const timer = canvasViewer ? undefined : window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, 5000);
    const whenVisible = () => { if (document.visibilityState === "visible") void refresh(); };
    window.addEventListener("focus", refresh);
    if (canvasViewer) document.addEventListener("visibilitychange", whenVisible);
    return () => {
      document.removeEventListener("visibilitychange", whenVisible);
      window.clearInterval(timer);
      window.removeEventListener("focus", refresh);
    };
  }, [canvasViewer, refresh]);
  useEffect(() => {
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
      setEditor(null);
      setTrash(false);
      setEntry(null);
    };
    window.addEventListener("popstate", back);
    window.addEventListener("hashchange", back);
    return () => {
      ++seq.current;
      window.removeEventListener("popstate", back);
      window.removeEventListener("hashchange", back);
    };
  }, []);
  useEffect(() => {
    if (!db || canvasViewer) return;
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
    setPage("projects");
    setRoute("#projects");
    activeURL.current = location.origin + location.pathname + location.search + "#projects";
    history.replaceState({}, "", "#projects");
  }, [db, canvasViewer, page, recordRoute, requestedProject, scope, routeTarget, viewerProfile, route, activeProject]);
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
    const path = p === "projects"
      ? "#projects"
      : `#project/${encodeURIComponent(nextScope)}/${p}` + (p === "tickets" && nextView ? "/" + nextView : "");
    const hash = p === "tickets" ? withMilestoneTicketFilter(path, milestoneId) : path;
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
  }
  const milestone = (id: string) => go("tickets", "", id);
  function filterTicketsByMilestone(id: string) {
    const hash = withMilestoneTicketFilter(`#project/${encodeURIComponent(selectedProjectId)}/tickets${ticketView ? "/" + ticketView : ""}`, id);
    setRoute(hash);
    history.replaceState(history.state, "", hash);
    activeURL.current = location.href;
  }
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
  if (canvasViewer) {
    if (!db && !error) return <div className="canvas-viewer-message">Loading canvas…</div>;
    const version = routeParts(route)[requestedProject ? 4 : 2] || "";
    return db && viewerProfile ? <DesignCanvas key={id + "/" + version} db={db} document={viewerProfile} viewer version={version} /> :
      <div className="canvas-viewer-message"><p>{error || "This canvas is unavailable."}</p>
        <a href={requestedProject ? `#project/${encodeURIComponent(requestedProject)}/canvas` : "#projects"}>Back to {requestedProject ? "canvases" : "projects"}</a></div>;
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
                  <Icon page={k === "canvas" ? "Design" : k === "assistant" ? "runs" : k} />
                  {k === "runs" ? "Runs & activity" : k === "assistant" ? "Project assistant" : names[k]}
                </button>
              ))}
            </Fragment>
          ))}
          <small>Help</small>
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
          {page !== "canvas" && page !== "projects" && page !== "assistant" && page !== "dashboard" && page !== "tickets" && <div className="heading">
            <div>
              <h1>{monitoring ? <>Runs <em>&amp;</em> activity</> : section}</h1>
              <p>
                {db
                    ? page === "activity"
                      ? (db.activity_count ?? db.activity.length) + " changes"
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
                key={[page, selectedProjectId, ticketView, routeTarget?.id].join(":")}
                db={db}
                page={page}
                scope={selectedProjectId}
                edit={setEditor}
                inspect={setEntry}
                milestoneFilter={milestoneFromTicketRoute(route)}
                onMilestoneFilter={filterTicketsByMilestone}
                onNewTicket={newRecord}
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
