import { useEffect, useState } from "react";

export function VisualPreview({ document, filename, digest }: { document: string; filename: string; digest: string }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    let objectUrl = "";
    async function load() {
      const response = await fetch(`/api/visuals/${encodeURIComponent(document)}/${encodeURIComponent(filename)}?v=${digest}`, {
        headers: { "X-AgentBoard-UI": "1" }, signal: controller.signal,
      });
      if (!response.ok) throw new Error(`Preview unavailable (${response.status})`);
      const blob = await response.blob();
      if (controller.signal.aborted) return;
      objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
    }
    load().catch(e => { if (!controller.signal.aborted) setError(String(e)); });
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [document, filename, digest]);
  return <figure className="visual-preview">
    {url ? <a href={url} target="_blank" rel="noreferrer"><img src={url} alt={filename} /></a> : <small>{error || "Loading preview…"}</small>}
    <figcaption>{filename}</figcaption>
  </figure>;
}
