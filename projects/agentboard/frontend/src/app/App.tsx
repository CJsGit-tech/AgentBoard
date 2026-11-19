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
  const { mode, paired, preview, pair, refresh } = useWorkspace();
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (mode === "connected" && !paired) return <main className="pair-screen"><section className="pair-panel">
    <h1>Connect to AgentBoard</h1><p>Enter the local access token shown by your AgentBoard server.</p>
    <form aria-label="Connect to AgentBoard" onSubmit={async (event) => { event.preventDefault(); setBusy(true); setError(""); try { await pair(token.trim()); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not connect. Check the token and try again."); } finally { setBusy(false); } }}>
      <label htmlFor="pairing-token">Local access token</label><input id="pairing-token" name="pairing_token" type="password" autoComplete="current-password" required value={token} onChange={e=>setToken(e.target.value)} />
      {error && <p role="alert" className="form-error">{error}</p>}<button className="primary" disabled={busy}>{busy ? "Connecting…" : "Connect"}</button>
    </form><small>Your token is sent to the configured local AgentBoard API.</small>
  </section></main>;
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
