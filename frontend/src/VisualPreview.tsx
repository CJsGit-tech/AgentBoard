import { useEffect, useRef, useState } from "react";

type PreviewProps = { document: string; filename: string; digest: string; thumbnail?: boolean };

export function VisualPreview({ document, filename, digest, thumbnail = false }: PreviewProps) {
  const figure = useRef<HTMLElement>(null);
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const query = new URLSearchParams({ preview: filename, digest });
  const originalHref = `#documents/${encodeURIComponent(document)}?${query}`;
  useEffect(() => {
    const controller = new AbortController();
    let objectUrl = "";
    setUrl("");
    setError("");
    async function load() {
      try {
        const path = `/api/visuals/${encodeURIComponent(document)}/${encodeURIComponent(filename)}`;
        const response = await fetch(`${path}${thumbnail ? "/thumbnail" : ""}?v=${digest}`, {
          headers: { "X-AgentBoard-UI": "1" }, signal: controller.signal,
        });
        if (!response.ok) throw new Error(`Preview unavailable (${response.status})`);
        const blob = await response.blob();
        if (!controller.signal.aborted) {
          objectUrl = URL.createObjectURL(blob);
          setUrl(objectUrl);
        }
      } catch (e) {
        if (!controller.signal.aborted) setError(e instanceof Error ? e.message : String(e));
      }
    }

    let observer: IntersectionObserver | undefined;
    if (thumbnail && figure.current && typeof IntersectionObserver !== "undefined") {
      observer = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) {
          observer?.disconnect();
          void load();
        }
      }, { rootMargin: "100px" });
      observer.observe(figure.current);
    } else if (!thumbnail) {
      void load();
    }
    return () => {
      observer?.disconnect();
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [document, filename, digest, thumbnail]);

  return <figure className="visual-preview" ref={figure}>
    {thumbnail ? <a className="screenshot-thumbnail" href={originalHref} aria-label={`Open original ${filename}`}>
      {url ? <img src={url} alt={filename} /> : <small>{error ? `${error} · Open original` : "Open original"}</small>}
    </a> : url ? <a href={url} target="_blank" rel="noreferrer"><img src={url} alt={filename} /></a>
      : <small>{error || "Loading preview…"}</small>}
    <figcaption>{filename}</figcaption>
  </figure>;
}
