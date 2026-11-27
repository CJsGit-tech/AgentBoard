import { Button, Drawer, NativeSelect, TextInput } from "@mantine/core";
import "./features/library/cards.css";
import "./features/library/canvas-viewer.css";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Icon } from "./Common";
import { InfoHelp } from "./features/help/InfoHelp";
import { type Row, type Workspace, nameOf, stamp } from "./model";
import { canvasPreviewGeometry, matchesCanvasPublication, verifiedScreenCount } from "./features/library/canvas-preview";
import { proofHref, resolveProof } from "./features/tickets/proof-links";

const canvasURL = (document: Row, version: number) => "#canvas/" + document.id + "/" + version;

function PublicationDelivery({ db, document, version }: { db: Workspace; document: Row; version: number }) {
  const tickets = db.tickets.filter(ticket => matchesCanvasPublication(ticket, document, version));
  const verified = tickets.flatMap(ticket => (ticket.criteria || []).flatMap(criterion => {
    if (criterion.design?.document_id !== document.id || criterion.design.version !== version) return [];
    return (criterion.evidence || []).flatMap(proof => {
      const source = proof.status === "verified" ? resolveProof(db, ticket, proof) : null;
      return source ? [{ proof, source, time: source.updated_at || source.created_at || "" }] : [];
    });
  }));
  const latest = verified.sort((left, right) => right.time.localeCompare(left.time))[0];

  return <div className="canvas-delivery">
    {tickets.length > 0 ? <details>
      <summary>Implementation tickets ({tickets.length})</summary>
      <ul>{tickets.map(ticket => <li key={ticket.id}><a href={`#tickets/${encodeURIComponent(ticket.id)}`}>{ticket.name}</a></li>)}</ul>
    </details> : <p>No implementation tickets linked to this version.</p>}
    {latest ? <p><a className="link" href={proofHref(latest.proof)}>{latest.time ? "Latest recorded verification" : "Verified evidence"}: {latest.source.name}</a></p>
      : tickets.length > 0 && <p>No verified criterion evidence linked to this version.</p>}
  </div>;
}

function PublicationHistory({ db, document, selected, choose }: {
  db?: Workspace; document: Row; selected: number; choose: (version: number) => void;
}) {
  return <>{(document.canvas_versions || []).map((version, index) =>
    <section className="canvas-history-entry" key={version.version}>
      <h3>Version {version.version}{index === 0 ? " · Latest" : ""}</h3>
      <p>{version.change_note || "Published before change notes were recorded."}</p>
      <p className="canvas-publication-byline">{stamp(version.published_at)}{version.publisher && " · " + version.publisher}</p>
      <h4>Source documents</h4>
      {version.sources.length ? <ul>{version.sources.map(source =>
        <li key={source.document_id}>{source.name} · Revision {source.revision}</li>,
      )}</ul> : <p>Source revisions were not recorded for this publication.</p>}
      <p>Screens: {verifiedScreenCount(version.screen_count)}</p>
      {db && <PublicationDelivery db={db} document={document} version={version.version} />}
      {selected === version.version ? <small>Selected publication</small> :
        <Button size="xs" variant="default" onClick={() => choose(version.version)}>View version {version.version}</Button>}
    </section>,
  )}</>;
}

function CanvasPreview({ asset, title, fit, active }: { asset: string; title: string; fit: boolean; active: boolean }) {
  const stage = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [attempt, setAttempt] = useState(0);
  const [mounted, setMounted] = useState(false);
  const loaded = useRef(false);
  const [state, setState] = useState<"checking" | "loading" | "ready" | "failed">("checking");
  const url = `/canvas-content/${encodeURIComponent(asset)}/gallery.html`;

  useLayoutEffect(() => {
    const element = stage.current;
    if (!element) return;
    const measure = () => {
      if (element.clientWidth && element.clientHeight) setSize({ width: element.clientWidth, height: element.clientHeight });
    };
    const observer = new ResizeObserver(measure);
    measure();
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  // A sandboxed frame can fire load on a 404. Recheck availability before revealing even a retained frame.
  useLayoutEffect(() => {
    setState("checking");
    if (!active) return;
    const controller = new AbortController();
    const fail = () => {
      loaded.current = false;
      setMounted(false);
      setState("failed");
    };
    const timeout = window.setTimeout(() => { controller.abort(); fail(); }, 15000);
    void fetch(url, { method: "HEAD", cache: "no-store", signal: controller.signal }).then(response => {
      if (controller.signal.aborted) return;
      if (!response.ok || !response.headers.get("content-type")?.startsWith("text/html")) {
        fail();
        return;
      }
      setMounted(true);
      setState(loaded.current ? "ready" : "loading");
    }).catch(() => {
      if (!controller.signal.aborted) fail();
    }).finally(() => window.clearTimeout(timeout));
    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [url, attempt, active]);

  useEffect(() => {
    if (!active || state !== "loading") return;
    const timeout = window.setTimeout(() => {
      loaded.current = false;
      setMounted(false);
      setState("failed");
    }, 15000);
    return () => window.clearTimeout(timeout);
  }, [state, active]);

  const geometry = canvasPreviewGeometry(size.width, size.height, fit);
  return <div className="canvas-preview-stage" hidden={!active} ref={stage} aria-busy={state === "checking" || state === "loading"}>
    {(state === "checking" || state === "loading") && <p className="canvas-preview-message" role="status">Loading preview…</p>}
    {state === "failed" && <div className="canvas-preview-message" role="alert">
      <p>The published preview could not be loaded.</p>
      <Button size="xs" variant="default" onClick={() => { setState("checking"); setAttempt(value => value + 1); }}>Retry preview</Button>
    </div>}
    {mounted && <iframe title={title} src={url} hidden={!active || state === "checking"}
      className="canvas-preview-frame" style={{ width: geometry.width, height: geometry.height, transform: `translateX(-50%) scale(${geometry.scale})` }}
      sandbox="allow-scripts allow-forms" referrerPolicy="no-referrer" onLoad={() => {
        loaded.current = true;
        setState(current => current === "loading" ? "ready" : current);
      }} onError={() => { loaded.current = false; setMounted(false); setState("failed"); }} />}
  </div>;
}

export function DesignCanvas({ db, document, viewer = false, version = "" }: { db?: Workspace; document: Row; viewer?: boolean; version?: string }) {
  const versions = document.canvas_versions || [];
  const [selection, setSelection] = useState(version);
  const [previous, setPrevious] = useState("");
  const [history, showHistory] = useState(false);
  const [fit, setFit] = useState(true);
  const selected = selection ? versions.find(item => String(item.version) === selection) : versions[0];
  if (!selected) return <div className="canvas-viewer-message"><p>This canvas version is unavailable.</p><a href={`#project/${encodeURIComponent(document.project || "")}/canvas`}>Back to canvases</a></div>;

  function choose(version: number) {
    if (viewer && selected && selected.version !== version) setPrevious(selected.asset_key);
    setSelection(String(version));
    if (viewer) window.history.replaceState({}, "", canvasURL(document, version));
    showHistory(false);
  }

  return <div className={viewer ? "canvas-viewer" : "canvas-profile"}>
    <div className="canvas-workspace-bar">
      {viewer ? <div className="canvas-viewer-name"><a href={"#documents/" + document.id}>{document.name}</a>
        {db && <small>{nameOf(db, "projects", document.project)}</small>}</div> : <h3>Design Canvas</h3>}
      <div className="canvas-reader-actions">
        {!viewer && <a className="canvas-open" href={canvasURL(document, selected.version)} target="_blank" rel="noreferrer">Open canvas <Icon page="arrow" /></a>}
        <NativeSelect aria-label="Canvas version" value={String(selected.version)}
          onChange={event => choose(Number(event.currentTarget.value))}
          data={versions.map(item => ({ value: String(item.version), label: "Version " + item.version }))} />
        <Button size="xs" variant="default" onClick={() => showHistory(true)}>Version history</Button>
        {viewer && <Button size="xs" variant={fit ? "light" : "default"} aria-pressed={fit} onClick={() => setFit(value => !value)}>Fit to viewport</Button>}
      </div>
    </div>
    {viewer && <>
      <div className="canvas-viewer-delivery"><span>Screens: {verifiedScreenCount(selected.screen_count)}</span>
        {db && <PublicationDelivery db={db} document={document} version={selected.version} />}</div>
      {/* Keep the two most recent frames in publication order. Moving a live iframe reloads it. */}
      {versions.filter(item => item.asset_key === selected.asset_key || item.asset_key === previous).map(item =>
        <CanvasPreview key={item.asset_key} asset={item.asset_key} active={item.asset_key === selected.asset_key}
          title={document.name + " canvas"} fit={fit} />)}
    </>}
    <Drawer opened={history} onClose={() => showHistory(false)} title="Canvas version history" closeButtonProps={{ "aria-label": "Close version history" }} position="right" size="md">
      <PublicationHistory db={db} document={document} selected={selected.version} choose={choose} />
    </Drawer>
  </div>;
}

export function CanvasWorkspace({ db, scope }: { db: Workspace; scope: string }) {
  const [query, setQuery] = useState("");
  const [history, showHistory] = useState<{ document: Row; version: number } | null>(null);
  const documents = db.documents.filter(doc => doc.canvas_versions?.length && (!scope || doc.project === scope));
  const publications = documents.flatMap(document => document.canvas_versions!.map(version => ({ document, version })));
  const term = query.trim().toLowerCase();
  const matches = publications.filter(({ document, version }) =>
    [document.name, nameOf(db, "projects", document.project), "Version " + version.version, version.publisher || ""]
      .join(" ").toLowerCase().includes(term),
  );

  return <>
    <div className="heading"><div><div className="with-info"><h1>Canvas</h1><InfoHelp label="canvas publication">Reviewed local drafts appear here after publication on Design Profile.</InfoHelp></div><p>{publications.length} published {publications.length === 1 ? "version" : "versions"} · {scope ? nameOf(db, "projects", scope) : "All projects"}</p></div></div>
    <div className="folder-tools">
      <TextInput type="search" aria-label="Search canvases" placeholder="Search canvases…" leftSection={<Icon page="search" />}
        value={query} onChange={event => setQuery(event.currentTarget.value)} />
      <p className="folder-summary"><b>{matches.length}</b> {matches.length === 1 ? "version" : "versions"}</p>
    </div>
    <div className="folders is-canvas">{matches.map(({ document, version }) =>
      <article className="folder" key={document.id + "/" + version.version}>
        <div className="folder-tab">Version {version.version}{document.canvas_versions![0].version === version.version ? " · Latest" : ""}</div>
        <div className="folder-body">
          <div className="folder-head"><h2><a className="folder-title" href={canvasURL(document, version.version)}
            target="_blank" rel="noreferrer" aria-label={document.name + " canvas · Version " + version.version}>
            {document.name} canvas <Icon page="arrow" /></a></h2></div>
          <p className="folder-description">{nameOf(db, "projects", document.project)}</p>
          <div className="canvas-publication-meta">
            <p><span>Published</span> <b>{stamp(version.published_at)}</b></p>
            <p><span>Publisher</span> <b>{version.publisher || "Not recorded"}</b></p>
            <p><span>Screens</span> <b>{verifiedScreenCount(version.screen_count)}</b></p>
          </div>
          <p className="canvas-card-note">{version.change_note || "Publication notes were not recorded."}</p>
          <PublicationDelivery db={db} document={document} version={version.version} />
          <div className="folder-foot">
            <a className="ghost-link" href={"#documents/" + document.id}>Design Profile <Icon page="arrow" /></a>
            <button className="link ghost-link" onClick={() => showHistory({ document, version: version.version })}>Version history</button>
          </div>
        </div>
      </article>,
    )}</div>
    {!matches.length && <div className="folder-empty">
      <h2>{publications.length ? "No matching canvases" : "No published canvases yet"}</h2>
      {publications.length > 0 && <button className="link" onClick={() => setQuery("")}>Clear search</button>}
    </div>}
    <Drawer opened={!!history} onClose={() => showHistory(null)} title="Canvas version history" closeButtonProps={{ "aria-label": "Close version history" }} position="right" size="md">
      {history && <PublicationHistory db={db} document={history.document} selected={history.version} choose={version => {
        window.open(canvasURL(history.document, version), "_blank", "noopener,noreferrer");
        showHistory(null);
      }} />}
    </Drawer>
  </>;
}
