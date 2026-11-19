import {
  LayoutDashboard,
  PanelsTopLeft,
  UsersRound,
  FileText,
  Activity,
  FolderOpen,
  Bot,
} from "lucide-react";
import { useWorkspace } from "../app/WorkspaceContext";
export function Sidebar({ route }: { route: string }) {
  const { db, projectId, selectProject, navigate } = useWorkspace();
  const links = [
    ["Overview", "/overview", LayoutDashboard],
    ["Tickets", "/tickets", PanelsTopLeft],
    ["Roles", "/roles", UsersRound],
    ["Documents", "/documents", FileText],
    ["Activity", "/activity", Activity],
    ["Playground", "/runs", Bot],
  ] as const;
  return (
    <aside className="sidebar">
      <a
        href="#/overview"
        className="brand"
        onClick={(e) => {
          e.preventDefault();
          navigate("/overview");
        }}
      >
        <b>a</b>
        <span>AgentBoard</span>
      </a>
      <small className="workspace-label">WORKSPACE</small>
      <label htmlFor="sidebar-1" className="project-picker">
        <span className="sr-only">Select project</span>
        <select
          id="sidebar-1"
          aria-label="Select project"
          value={projectId}
          onChange={(e) => selectProject(e.target.value)}
        >
          {db.projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} · {p.id.slice(0, 8)}
            </option>
          ))}
        </select>
      </label>
      <nav aria-label="Project navigation">
        {links.map(([name, path, Icon]) => (
          <a
            key={path}
            href={"#" + path}
            title={name}
            aria-label={name}
            aria-current={route.startsWith(path) ? "page" : undefined}
            onClick={(e) => {
              e.preventDefault();
              navigate(path);
            }}
          >
            <Icon size={18} />
            <span>{name}</span>
          </a>
        ))}
      </nav>
      <a
        className="all-projects"
        aria-label="All projects"
        href="#/projects"
        onClick={(e) => {
          e.preventDefault();
          navigate("/projects");
        }}
      >
        <FolderOpen size={16} />
        <span>All projects</span>
      </a>
      <div className="sidebar-bottom">
        <i />
        Local workspace<small>Personal · single user</small>
      </div>
    </aside>
  );
}
