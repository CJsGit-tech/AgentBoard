import { useEffect, useState } from "react";
import { errorText, type Workspace } from "../../model";
import { conditionalRead, type Snapshot } from "./conditional-read";

/** Project settings and the project picker can open outside a loaded project's scope. */
export function useEditorWorkspace(path?: string) {
  const [snapshot, setSnapshot] = useState<Snapshot<Workspace>>();
  const [error, setError] = useState("");
  const [attempt, retry] = useState(0);
  useEffect(() => {
    setError("");
    if (!path) return;
    let live = true, reading = false;
    let previous: Snapshot<Workspace> | undefined;
    async function read() {
      if (!path || reading || document.visibilityState !== "visible") return;
      reading = true;
      try {
        const snapshot = await conditionalRead<Workspace>(path, previous);
        if (live) { previous = snapshot; setSnapshot(snapshot); setError(""); }
      } catch (e) { if (live) setError(errorText(e)); }
      finally { reading = false; }
    }
    void read();
    const timer = window.setInterval(read, 5000);
    window.addEventListener("focus", read);
    return () => { live = false; window.clearInterval(timer); window.removeEventListener("focus", read); };
  }, [path, attempt]);
  return { data: path && snapshot?.path === path ? snapshot.data : undefined, error, retry: () => retry(n => n + 1) };
}
