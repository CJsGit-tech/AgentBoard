import { useEffect, useRef, useState } from "react";
import { useWorkspace } from "./WorkspaceContext";

export function useRoute() {
  const { hasUnsavedChanges, setDirty } = useWorkspace();
  const [route, setRoute] = useState(location.hash.slice(1) || "/overview");
  const currentRoute = useRef(route);

  useEffect(() => {
    const listener = () => {
      const next = location.hash.slice(1) || "/overview";
      if (next === currentRoute.current) return;
      if (hasUnsavedChanges() && !confirm("Discard unsaved changes?")) {
        // Back/Forward and direct hash navigation must protect the same draft
        // as in-app navigation. Replacing the URL does not emit hashchange.
        history.replaceState(null, "", "#" + currentRoute.current);
        return;
      }
      setDirty(false);
      currentRoute.current = next;
      setRoute(next);
    };
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, [hasUnsavedChanges, setDirty]);
  return route;
}
