import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { Database, Doc, Project, Revision, Role, Ticket } from "../api/types";
import { fixtures } from "../api/fixtures";
import { id, retained, timestamp } from "../api/mockAdapter";
import * as api from "../api/restClient";

type Preview = "Ready" | "Loading" | "Empty" | "Error" | "Conflict" | "Disconnected";
type Mode = "mock" | "connected";

interface Context {
  db: Database;
  projectId: string;
  selectProject: (id: string) => void;
  preview: Preview;
  setPreview: (state: Preview) => void;
  failNext: boolean;
  setFailNext: (value: boolean) => void;
  mode: Mode;
  paired: boolean;
  liveConnected: boolean;
  liveResync: boolean;
  clearLiveResync: () => void;
  pair: (token: string) => Promise<void>;
  commit: (change: (db: Database) => Database, action: string, ticketId?: string) => boolean;
  saveProject: (values: { name: string; purpose: string }, current?: Project) => Promise<string>;
  deleteProject: (project: Project) => Promise<void>;
  saveRole: (values: { name: string; responsibilities: string }, current?: Role) => Promise<string>;
  saveTicket: (values: any, current?: Ticket) => Promise<string>;
  saveDocument: (values: any, current?: Doc, source?: "manual" | "upload", sourceId?: string) => Promise<string>;
  restoreDocument: (document: Doc, revision: Revision) => Promise<void>;
  linkDocument: (ticket: Ticket, documentId: string, relation: "Context" | "Output") => Promise<void>;
  unlinkDocument: (ticket: Ticket, documentId: string, relation: "Context" | "Output") => Promise<void>;
  refresh: (projectId?: string) => Promise<void>;
  notice: string;
  clearNotice: () => void;
  dirty: boolean;
  setDirty: (value: boolean) => void;
  navigate: (path: string) => void;
  reset: () => void;
}

const Workspace = createContext<Context | null>(null);
const configuredMode = (import.meta as any).env?.VITE_AGENTBOARD_MODE as Mode | undefined;
const mode: Mode = configuredMode || ((import.meta as any).env?.DEV ? "mock" : "connected");
const activeProjectKey = "agentboard-active-project";

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [db, setDb] = useState<Database>(fixtures);
  const [projectId, setProject] = useState(() => mode === "connected" ? localStorage.getItem(activeProjectKey) || "" : "agentboard");
  const [preview, setPreview] = useState<Preview>(mode === "connected" ? "Loading" : "Ready");
  const [paired, setPaired] = useState(mode === "mock");
  const [liveConnected, setLiveConnected] = useState(false);
  const [liveResync, setLiveResync] = useState(false);
  const [failNext, setFailNext] = useState(false);
  const [notice, setNotice] = useState("");
  const [dirty, setDirtyState] = useState(false);
  const dirtyRef = useRef(false);
  const dirtyProjectRef = useRef("");
  const activeProjectRef = useRef(projectId);
  const refreshStateRef = useRef<{ promise: Promise<void> | null; requestedProjectId: string | null }>({ promise: null, requestedProjectId: null });

  const setDirty = (value: boolean) => {
    dirtyRef.current = value;
    setDirtyState(value);
  };

  const refresh = useCallback(async (selectedId = projectId) => {
    const refreshState = refreshStateRef.current;
    refreshState.requestedProjectId = selectedId;
    if (refreshState.promise) {
      await refreshState.promise;
      const queuedId = refreshState.requestedProjectId;
      if (queuedId !== null) {
        refreshState.requestedProjectId = null;
        await refresh(queuedId);
      }
      return;
    }

    const worker = (async () => {
      while (refreshState.requestedProjectId !== null) {
        const requestedId = refreshState.requestedProjectId;
        refreshState.requestedProjectId = null;
        const next = await api.loadDatabase(requestedId);
        if (activeProjectRef.current && activeProjectRef.current !== requestedId) continue;
        setDb(next);
        const activeId = next.projects.some((project) => project.id === requestedId) ? requestedId : next.projects[0]?.id || "";
        activeProjectRef.current = activeId;
        setProject(activeId);
        if (activeId) localStorage.setItem(activeProjectKey, activeId);
        else localStorage.removeItem(activeProjectKey);
        setPreview(next.projects.length ? "Ready" : "Empty");
      }
    })();
    refreshState.promise = worker;
    try {
      await worker;
    } finally {
      if (refreshState.promise === worker) refreshState.promise = null;
    }
    const queuedId = refreshState.requestedProjectId;
    if (queuedId !== null) {
      refreshState.requestedProjectId = null;
      await refresh(queuedId);
    }
  }, [projectId]);

  useEffect(() => {
    if (mode !== "connected") return;
    let active = true;
    const preferredId = localStorage.getItem(activeProjectKey) || undefined;
    api.restoreSession()
      .then(() => api.loadDatabase(preferredId))
      .then((next) => {
        if (!active) return;
        setDb(next);
        const activeId = next.projects.some((project) => project.id === preferredId) ? preferredId! : next.projects[0]?.id || "";
        activeProjectRef.current = activeId;
        setProject(activeId);
        if (activeId) localStorage.setItem(activeProjectKey, activeId);
        else localStorage.removeItem(activeProjectKey);
        setPaired(true);
        setPreview(next.projects.length ? "Ready" : "Empty");
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof api.ApiError && error.status === 401) {
          setPaired(false);
          setPreview("Disconnected");
        } else {
          setPreview("Error");
          setNotice(error instanceof Error ? error.message : "Could not connect to AgentBoard.");
        }
      });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (mode !== "connected" || !paired || !projectId) {
      setLiveConnected(false);
      return;
    }
    const base = ((import.meta as any).env?.VITE_AGENTBOARD_API_BASE || "").replace(/\/$/, "");
    const source = new EventSource(`${base}/events?project_id=${encodeURIComponent(projectId)}`, { withCredentials: true });
    source.onopen = () => setLiveConnected(true);
    source.onerror = () => setLiveConnected(false);
    source.addEventListener("activity", () => { void refresh(projectId).catch(() => setLiveConnected(false)); });
    source.addEventListener("resync", () => {
      setLiveResync(true);
      void refresh(projectId).catch(() => setLiveConnected(false));
    });
    return () => source.close();
  }, [mode, paired, projectId, refresh]);

  const pair = async (token: string) => {
    await api.pair(token);
    await refresh();
    setPaired(true);
    setNotice("Connected to AgentBoard.");
  };

  const selectProject = (nextId: string) => {
    if (dirtyRef.current && !confirm("Discard unsaved changes before switching projects?")) return;
    setDirty(false);
    setProject(nextId);
    activeProjectRef.current = nextId;
    if (mode === "connected") localStorage.setItem(activeProjectKey, nextId);
    location.hash = "/overview";
    if (mode !== "connected") {
      setPreview("Ready");
      return;
    }
    dirtyProjectRef.current = nextId;
    setPreview("Loading");
    void api.loadDatabase(nextId).then((next) => {
      if (dirtyProjectRef.current !== nextId) return;
      setDb(next);
      activeProjectRef.current = nextId;
      setPreview(next.projects.length ? "Ready" : "Empty");
    }).catch((error: unknown) => {
      if (dirtyProjectRef.current !== nextId) return;
      setPreview("Error");
      setNotice(error instanceof Error ? error.message : "Could not load project.");
    });
  };

  const navigate = (path: string) => {
    if (dirtyRef.current && !confirm("Discard unsaved changes?")) return;
    setDirty(false);
    location.hash = path;
  };

  const commit = (change: (data: Database) => Database, action: string, ticketId?: string) => {
    if (mode === "connected") {
      setNotice("Use a connected save control to update this record.");
      return false;
    }
    if (failNext) {
      setFailNext(false);
      setNotice("Save failed. Your input is retained. Try again.");
      return false;
    }
    if (preview === "Conflict") {
      setNotice("Conflict: a newer record exists. Your draft is retained; review the current record before retrying.");
      return false;
    }
    setDb((current) => {
      let next = change(current);
      if (action) {
        next = {
          ...next,
          activity: [{
            id: id("event"), projectId, ticketId, agent: "Me", action,
            type: "Record change", label: "local", outcome: "Succeeded",
            provenance: "Server-observed", time: timestamp(),
          }, ...retained(next.activity)],
        };
      }
      return next;
    });
    setDirty(false);
    setNotice("Saved in preview memory only.");
    return true;
  };

  const execute = async <T,>(operation: () => Promise<T>, successMessage: string): Promise<T> => {
    if (failNext) {
      setFailNext(false);
      throw new Error("Save failed. Your input is retained. Try again.");
    }
    try {
      const result = await operation();
      await refresh();
      setDirty(false);
      setNotice(successMessage);
      return result;
    } catch (error) {
      if (error instanceof api.ApiError && error.status === 409) setPreview("Conflict");
      setNotice(error instanceof Error ? error.message : "Save failed. Your draft is retained.");
      throw error;
    }
  };

  const requirePreviewSave = (saved: boolean) => {
    if (!saved) throw new Error("Save failed. Your draft is retained.");
  };

  const saveProject = async (values: { name: string; purpose: string }, current?: Project) => {
    if (mode === "connected") {
      const saved = await execute(() => current ? api.updateProject(current, values) : api.createProject(values), "Project saved to AgentBoard.");
      return saved.id;
    }
    const idValue = current?.id || id("project");
    requirePreviewSave(commit((data) => ({
      ...data,
      projects: current
        ? data.projects.map((item) => item.id === idValue ? { ...item, ...values, updated: timestamp() } : item)
        : [...data.projects, { id: idValue, ...values, updated: timestamp() }],
    }), current ? "Updated project" : "Created project"));
    return idValue;
  };

  const deleteProject = async (project: Project) => {
    const previousActiveId = projectId;
    if (mode === "connected") {
      // Only change local state after the server confirms the destructive operation.
      await api.deleteProject(project);
      const remaining = db.projects.filter((item) => item.id !== project.id);
      const nextActiveId = previousActiveId === project.id ? remaining[0]?.id || "" : previousActiveId;
      setDb((current) => ({
        ...current,
        projects: current.projects.filter((item) => item.id !== project.id),
        roles: current.roles.filter((item) => item.projectId !== project.id),
        tickets: current.tickets.filter((item) => item.projectId !== project.id),
        documents: current.documents.filter((item) => item.projectId !== project.id),
        activity: current.activity.filter((item) => item.projectId !== project.id),
        approvals: current.approvals.filter((item) => current.tickets.some((ticket) => ticket.id === item.ticketId && ticket.projectId !== project.id)),
      }));
      if (previousActiveId === project.id) {
        setProject(nextActiveId);
        activeProjectRef.current = nextActiveId;
        dirtyProjectRef.current = nextActiveId;
        if (nextActiveId) localStorage.setItem(activeProjectKey, nextActiveId);
        else localStorage.removeItem(activeProjectKey);
        if (nextActiveId) {
          setPreview("Loading");
          try {
            const next = await api.loadDatabase(nextActiveId);
            if (activeProjectRef.current === nextActiveId) {
              setDb(next);
              setPreview(next.projects.length ? "Ready" : "Empty");
            }
          } catch (error) {
            setPreview("Error");
            setNotice(error instanceof Error ? error.message : "Project deleted, but the next project could not be loaded.");
          }
        } else {
          setPreview("Empty");
          setDb((current) => ({ ...current, roles: [], tickets: [], documents: [], activity: [], approvals: [] }));
        }
      }
      setNotice("Project deleted with its associated records.");
    } else {
      if (failNext) {
        setFailNext(false);
        throw new Error("Delete failed. The project and its records are unchanged. Try again.");
      }
      const remaining = db.projects.filter((item) => item.id !== project.id);
      const nextActiveId = previousActiveId === project.id ? remaining[0]?.id || "" : previousActiveId;
      const ticketIds = new Set(db.tickets.filter((item) => item.projectId === project.id).map((item) => item.id));
      setDb((current) => ({
        ...current,
        projects: current.projects.filter((item) => item.id !== project.id),
        roles: current.roles.filter((item) => item.projectId !== project.id),
        tickets: current.tickets.filter((item) => item.projectId !== project.id),
        documents: current.documents.filter((item) => item.projectId !== project.id),
        activity: current.activity.filter((item) => item.projectId !== project.id),
        approvals: current.approvals.filter((item) => !ticketIds.has(item.ticketId)),
      }));
      if (previousActiveId === project.id) {
        setProject(nextActiveId);
        activeProjectRef.current = nextActiveId;
        if (nextActiveId) localStorage.setItem(activeProjectKey, nextActiveId);
        else localStorage.removeItem(activeProjectKey);
        location.hash = "/projects";
        setPreview(remaining.length ? "Ready" : "Empty");
      }
      setNotice("Project deleted with its associated records in this preview.");
    }
    setDirty(false);
  };

  const saveRole = async (values: { name: string; responsibilities: string }, current?: Role) => {
    if (mode === "connected") {
      const saved = await execute(() => current ? api.updateRole(projectId, current, values) : api.createRole(projectId, values), "Role saved to AgentBoard.");
      return saved.id;
    }
    const idValue = current?.id || id("role");
    requirePreviewSave(commit((data) => ({
      ...data,
      roles: current
        ? data.roles.map((item) => item.id === idValue ? { ...item, ...values } : item)
        : [...data.roles, { id: idValue, projectId, ...values }],
    }), current ? "Updated role responsibilities" : "Created role"));
    return idValue;
  };

  const saveTicket = async (values: any, current?: Ticket) => {
    if (mode === "connected") {
      const saved = await execute(() => current ? api.updateTicket(projectId, current, values) : api.createTicket(projectId, values), "Ticket saved to AgentBoard.");
      return saved.id;
    }
    const idValue = current?.id || id("ticket");
    const ownerName = (ownerId: string) => ownerId === "me" ? "Me" : db.roles.find((role) => role.id === ownerId)?.name || ownerId || "Unassigned";
    const changes = current ? [
      current.status !== values.status ? `Status: ${current.status} → ${values.status}` : "",
      current.ownerId !== values.ownerId ? `Owner: ${ownerName(current.ownerId)} → ${ownerName(values.ownerId)}` : "",
    ].filter(Boolean).join("; ") : "Created ticket";
    requirePreviewSave(commit((data) => ({
      ...data,
      tickets: current
        ? data.tickets.map((item) => item.id === idValue ? { ...item, ...values, updated: timestamp() } : item)
        : [{ id: idValue, projectId, ...values, links: [], updated: timestamp() }, ...data.tickets],
    }), changes || "Updated ticket", idValue));
    return idValue;
  };

  const saveDocument = async (values: any, current?: Doc, source: "manual" | "upload" = "manual", sourceId?: string) => {
    if (mode === "connected") {
      const saved = await execute(() => current ? api.updateDocument(projectId, current, values) : api.createDocument(projectId, values, source, sourceId), "Document saved to AgentBoard.");
      return saved.id;
    }
    const idValue = current?.id || id("doc");
    const revision = { id: id("rev"), number: (current?.revisions[0]?.number || 0) + 1, content: values.content, updated: timestamp(), author: "Me" };
    requirePreviewSave(commit((data) => ({
      ...data,
      documents: current
        ? data.documents.map((item) => item.id === idValue ? { ...item, ...values, revisions: [revision, ...item.revisions] } : item)
        : [{ id: idValue, projectId, ...values, sourceFilename: source === "upload" ? sourceId : undefined, uploadedAt: source === "upload" ? timestamp() : undefined, revisions: [revision] }, ...data.documents],
    }), current ? "Revised document" : "Created document"));
    return idValue;
  };

  const restoreDocument = async (document: Doc, revision: Revision) => {
    if (mode === "connected") {
      await execute(() => api.restoreDocument(projectId, document, revision), "Document revision restored.");
      return;
    }
    const nextRevision = { ...revision, id: id("rev"), number: document.revisions[0].number + 1, author: "Me", updated: timestamp() };
    requirePreviewSave(commit((data) => ({
      ...data,
      documents: data.documents.map((item) => item.id === document.id ? { ...item, revisions: [nextRevision, ...item.revisions].slice(0, 4) } : item),
    }), `Restored document version ${revision.number}`));
  };

  const linkDocument = async (ticket: Ticket, documentId: string, relation: "Context" | "Output") => {
    if (mode === "connected") {
      await execute(() => api.linkDocument(projectId, ticket, documentId, relation), "Document linked.");
      return;
    }
    requirePreviewSave(commit((data) => ({
      ...data,
      tickets: data.tickets.map((item) => item.id === ticket.id ? { ...item, links: [...item.links, { documentId, relation }] } : item),
    }), `Linked document as ${relation}`, ticket.id));
  };

  const unlinkDocument = async (ticket: Ticket, documentId: string, relation: "Context" | "Output") => {
    if (mode === "connected") {
      await execute(() => api.unlinkDocument(projectId, ticket, documentId, relation), "Document unlinked.");
      return;
    }
    requirePreviewSave(commit((data) => ({
      ...data,
      tickets: data.tickets.map((item) => item.id === ticket.id ? {
        ...item, links: item.links.filter((link) => link.documentId !== documentId || link.relation !== relation),
      } : item),
    }), "Removed document link", ticket.id));
  };

  const reset = () => {
    if (mode === "connected") {
      void refresh().then(() => setNotice("Workspace refreshed."));
      return;
    }
    setDb(fixtures());
    setProject("agentboard");
    setDirty(false);
    setPreview("Ready");
    setNotice("Sample data reset.");
    location.hash = "/overview";
  };

  const value: Context = {
    db, projectId, selectProject, preview, setPreview, failNext, setFailNext,
    mode, paired, liveConnected, liveResync, clearLiveResync: () => setLiveResync(false), pair, commit, saveProject, deleteProject, saveRole, saveTicket, saveDocument,
    restoreDocument, linkDocument, unlinkDocument, refresh, notice,
    clearNotice: () => setNotice(""), dirty, setDirty, navigate, reset,
  };
  return <Workspace.Provider value={value}>{children}</Workspace.Provider>;
}

export function useWorkspace() {
  const context = useContext(Workspace);
  if (!context) throw new Error("Workspace context missing");
  return context;
}
