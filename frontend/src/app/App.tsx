import { WorkspaceProvider, useWorkspace } from "./WorkspaceContext";
import { useRoute } from "./useRoute";
import { WorkspaceShell } from "../components/WorkspaceShell";
import { ProjectsScreen } from "../features/projects/ProjectsScreen";
import { OverviewScreen } from "../features/overview/OverviewScreen";
import { RolesScreen } from "../features/roles/RolesScreen";
import { TicketsScreen } from "../features/tickets/TicketsScreen";
import { DocumentsScreen } from "../features/documents/DocumentsScreen";
import { DocumentDetailScreen } from "../features/documents/DocumentDetailScreen";
import { DocumentHistoryScreen } from "../features/documents/DocumentHistoryScreen";
import { ActivityScreen } from "../features/activity/ActivityScreen";
import { RunsScreen } from "../features/runs/RunsScreen";
import { ReactNode, useState } from "react";
function Routes() {
  const route = useRoute();
  const { projectId } = useWorkspace();
  let screen;
  if (route.startsWith("/projects")) screen = <ProjectsScreen />;
  else if (route.startsWith("/overview")) screen = <OverviewScreen />;
  else if (route.startsWith("/roles")) screen = <RolesScreen />;
  else if (route.startsWith("/tickets"))
    screen = <TicketsScreen key={projectId} route={route} />;
  else if (/^\/documents\/[^/]+\/history/.test(route))
    screen = <DocumentHistoryScreen route={route} />;
  else if (/^\/documents\/[^/]+/.test(route))
    screen = <DocumentDetailScreen route={route} />;
  else if (route.startsWith("/documents")) screen = <DocumentsScreen />;
  else if (route.startsWith("/activity")) screen = <ActivityScreen />;
  else if (route.startsWith("/runs")) screen = <RunsScreen key={projectId} />;
  else
    screen = (
      <section className="state-panel">
        <h1>Page not found</h1>
        <a href="#/overview">Return to overview</a>
      </section>
    );
  return <WorkspaceShell route={route}>{screen}</WorkspaceShell>;
}
function ConnectedGate({ children }: { children: ReactNode }) {
  const { mode, preview, refresh } = useWorkspace();
  const [error, setError] = useState("");
  if (mode === "connected" && preview === "Loading") return <main className="pair-screen"><section className="pair-panel" role="status"><h1>Loading workspace…</h1></section></main>;
  if (mode === "connected" && preview === "Error") return <main className="pair-screen"><section className="pair-panel" role="alert"><h1>AgentBoard is unavailable</h1><p>{error || "The workspace could not be loaded."}</p><button className="primary" onClick={()=>void refresh().catch(e=>setError(e.message))}>Retry connection</button></section></main>;
  return <>{children}</>;
}
export function App() {
  return (
    <WorkspaceProvider>
      <ConnectedGate><Routes /></ConnectedGate>
    </WorkspaceProvider>
  );
}
