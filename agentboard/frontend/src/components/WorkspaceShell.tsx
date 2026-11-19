import { OperationNotice } from "./OperationNotice";
import { ReactNode, useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { PreviewToolbar } from "./PreviewToolbar";
import { useWorkspace } from "../app/WorkspaceContext";
export function WorkspaceShell({
  route,
  children,
}: {
  route: string;
  children: ReactNode;
}) {
  const { notice, clearNotice, dirty, mode } = useWorkspace();
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(clearNotice, 6000);
    return () => clearTimeout(timer);
  }, [notice]);
  useEffect(() => {
    const heading = document.querySelector("main h1");
    document.title = `${heading?.textContent || "Workspace"} · AgentBoard`;
  }, [route]);
  useEffect(() => {
    const listener = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", listener);
    return () => window.removeEventListener("beforeunload", listener);
  }, [dirty]);
  return (
    <>
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Skip to main content
      </a>
      <PreviewToolbar />
      <div className="workspace">
        <Sidebar route={route} />
        <main id="main-content" tabIndex={-1}>
          {children}
          <footer>
            <span>{mode === "mock" ? "Local preview · no real agent execution" : "Connected workspace · SDK runs available"}</span>
            <span>AgentBoard</span>
          </footer>
        </main>
      </div>
      <OperationNotice message={notice} onDismiss={clearNotice} />
    </>
  );
}
