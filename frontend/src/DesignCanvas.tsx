import { Button, Drawer, NativeSelect, TextInput } from "@mantine/core";
import "./features/library/cards.css";
import { useState } from "react";
import { Icon } from "./Common";
import { InfoHelp } from "./features/help/InfoHelp";
import { type Row, type Workspace, nameOf, stamp } from "./model";

const canvasURL = (document: Row, version: number) => "#canvas/" + document.id + "/" + version;

function PublicationHistory({ document, selected, choose }: {
  document: Row; selected: number; choose: (version: number) => void;
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
      {selected === version.version ? <small>Selected publication</small> :
        <Button size="xs" variant="default" onClick={() => choose(version.version)}>View version {version.version}</Button>}
    </section>,
  )}</>;
}

export function DesignCanvas({ document, viewer = false }: { document: Row; viewer?: boolean }) {
  const versions = document.canvas_versions || [];
  const [selection, setSelection] = useState(viewer ? location.hash.split("/")[2] || "" : "");
  const [history, showHistory] = useState(false);
  const selected = selection ? versions.find(item => String(item.version) === selection) : versions[0];
  if (!selected) return <div className="canvas-viewer-message"><p>This canvas version is unavailable.</p><a href="#canvas">Back to canvases</a></div>;

  function choose(version: number) {
    setSelection(String(version));
    if (viewer) window.history.replaceState({}, "", canvasURL(document, version));
    showHistory(false);
  }

  return <div className={viewer ? "canvas-viewer" : "canvas-profile"}>
    <div className="canvas-workspace-bar">
      {viewer ? <a href={"#documents/" + document.id}>{document.name}</a> : <h3>Design Canvas</h3>}
      <div className="canvas-reader-actions">
        {!viewer && <a className="canvas-open" href={canvasURL(document, selected.version)} target="_blank" rel="noreferrer">Open canvas <Icon page="arrow" /></a>}
        <NativeSelect aria-label="Canvas version" value={String(selected.version)}
          onChange={event => choose(Number(event.currentTarget.value))}
          data={versions.map(item => ({ value: String(item.version), label: "Version " + item.version }))} />
        <Button size="xs" variant="default" onClick={() => showHistory(true)}>Version history</Button>
      </div>
    </div>
    {viewer && <iframe title={document.name + " canvas"} src={"/canvas-content/" + selected.asset_key + "/gallery.html"}
      sandbox="allow-scripts allow-forms" referrerPolicy="no-referrer" />}
    <Drawer opened={history} onClose={() => showHistory(false)} title="Canvas version history" closeButtonProps={{ "aria-label": "Close version history" }} position="right" size="md">
      <PublicationHistory document={document} selected={selected.version} choose={choose} />
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
            <p><span>Screens</span> <b>{version.screen_count ?? "Not recorded"}</b></p>
          </div>
          <p className="canvas-card-note">{version.change_note || "Publication notes were not recorded."}</p>
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
      {history && <PublicationHistory document={history.document} selected={history.version} choose={version => {
        window.open(canvasURL(history.document, version), "_blank", "noopener,noreferrer");
        showHistory(null);
      }} />}
    </Drawer>
  </>;
}
