import { Empty, Icon, Tag } from "../../Common";
import { currentReview, nameOf, type DesignReference, type Row, type Workspace } from "../../model";
import { Markdown } from "../documents/Markdown";
import { designHref, proofHref, resolveProof } from "./proof-links";
import "./ticket-reader.css";

export type TicketView = "Summary" | "Context" | "Outputs" | "Runs";
const typeLabel = (row: Row) => row.work_type === "BUG" ? "Bug" : row.work_type === "BUILD" ? "Build" : "Unclassified";

/** V5 ticket panel content: property grid, design card, criteria checklist, and the Context/Outputs/Runs lists. */
export function TicketReader({ db, ticket, openRun, view = "Summary" }: { db: Workspace; ticket: Row; openRun: (run: Row) => void; view?: TicketView }) {
  const inProject = (row: Row) => row.project === ticket.project;
  const documents = db.documents.filter(inProject);
  const inputs = documents.filter(doc => ticket.documents?.includes(doc.id));
  const outputs = documents.filter(doc => ticket.output_documents?.includes(doc.id));
  const runs = db.runs.filter(run => inProject(run) && run.ticket === ticket.id);

  if (view === "Context") return <DocList docs={inputs} empty="No context documents linked." note="Approved requirements and designs this ticket is built against." />;
  if (view === "Outputs") return <DocList docs={outputs} empty="No output documents linked." note="Evidence and documents produced by this work." />;
  if (view === "Runs") return <div className="ticket-reader">
    {runs.length ? <ul className="ticket-list">{runs.map(run => <li key={run.id}>
      <button type="button" className="link" onClick={() => openRun(run)}>{run.name}</button>
      <span className="ticket-list__meta">{run.status && <Tag value={run.status} />}{run.agent && <small>{run.agent}{run.mode ? ` · ${run.mode}` : ""}</small>}</span>
    </li>)}</ul> : <Empty>No runs linked.</Empty>}
  </div>;

  const scopeReviewer = currentReview(db, ticket.id)?.reviewer;
  const text = ticket.description || "";
  const references = [...text.matchAll(/#(tickets\/(AB-[a-f0-9]{12})|canvas\/(D-[a-f0-9]{12})\/(\d+))/g)];
  const prerequisites = db.tickets.filter(row => row.id !== ticket.id && inProject(row) && references.some(match => match[2] === row.id));
  const designs = new Map<string, DesignReference>();
  for (const [, , , id, version] of references) if (id) {
    const ref = { document_id: id, version: Number(version) };
    if (documents.find(doc => doc.id === id)?.canvas_versions?.some(item => item.version === ref.version)) designs.set(designHref(ref), ref);
  }
  for (const criterion of ticket.criteria || []) if (criterion.design && documents.find(doc => doc.id === criterion.design?.document_id)?.canvas_versions?.some(v => v.version === criterion.design?.version)) {
    designs.set(designHref(criterion.design), criterion.design);
  }
  const recordHref = (id: string) => prerequisites.some(row => row.id === id) ? `#tickets/${id}` :
    documents.some(row => row.id === id) ? `#documents/${id}` : undefined;
  const criteria = (ticket.criteria || []).map(criterion => {
    const proofs = (criterion.evidence || []).map(proof => ({ proof, doc: resolveProof(db, ticket, proof) }));
    const verified = proofs.filter(({ proof, doc }) => proof.status === "verified" && doc);
    return { criterion, proofs, verified };
  });
  const verifiedCount = criteria.filter(item => item.verified.length).length;

  return <div className="ticket-reader">
    <dl className="ticket-props">
      <div><dt>Status</dt><dd><Tag value={ticket.status || "Unspecified"} /></dd></div>
      <div><dt>Milestone</dt><dd>{nameOf(db, "milestones", ticket.milestone)}</dd></div>
      <div><dt>Type</dt><dd><Icon page={ticket.work_type === "BUG" ? "bug" : "build"} /> {typeLabel(ticket)}</dd></div>
      <div><dt>Role</dt><dd>{ticket.role ? nameOf(db, "roles", ticket.role) : "No role set"}</dd></div>
      <div><dt>Assigned to</dt><dd className="is-muted">Not recorded</dd></div>
      {scopeReviewer && <div><dt>Scope checked by</dt><dd>{scopeReviewer}</dd></div>}
    </dl>
    {[...designs].map(([href, design]) => <a key={href} className="ticket-design-card" href={href}>
      <span className="ticket-design-card__icon"><Icon page="browse" /></span>
      <span><b>{nameOf(db, "documents", design.document_id)}</b><small>Pinned design · Canvas version {design.version}</small></span>
      <span aria-hidden="true">↗</span>
    </a>)}
    {prerequisites.length > 0 && <section><h3>Prerequisites</h3><ul>{prerequisites.map(row => <li key={row.id}><a href={`#tickets/${row.id}`}>{row.name}</a></li>)}</ul></section>}
    <section><h3>Work</h3>{text ? <Markdown text={text} resolveRecord={recordHref} /> : <Empty>No description recorded.</Empty>}</section>
    {criteria.length > 0 && <section>
      <div className="ticket-criteria-head"><h3>Acceptance criteria</h3><small>{verifiedCount} of {criteria.length} verified</small></div>
      <ol className="ticket-checklist">{criteria.map(({ criterion, proofs, verified }) => (
        <li key={criterion.id} data-verified={verified.length > 0 || undefined}>
          <span className="ticket-check" aria-hidden="true">{verified.length ? "✓" : "○"}</span>
          <div>
            <p>{criterion.text}</p>
            <div className="ticket-check__meta">
              <span className="sr-only">{verified.length ? "Verified." : criterion.evidence_required ? "Unverified, evidence required." : "Unverified."}</span>
              {verified[0] ? <a href={proofHref(verified[0].proof)}>Open proof</a> : <small>{criterion.evidence_required ? "Evidence required" : "No proof linked"}</small>}
              {proofs.length > 1 && <details><summary>{proofs.length} proofs</summary><ul>{proofs.map(({ proof, doc }, index) => <li key={`${proofHref(proof)}:${index}`}>
                {doc ? <a href={proofHref(proof)}>{proof.kind === "screenshot" ? proof.filename : doc.name}</a> : "Recorded proof unavailable"}
                {proof.status === "superseded" ? " · Superseded" : proof.status === "unverified" ? " · Unverified" : ""}
              </li>)}</ul></details>}
              {criterion.design && <a href={designHref(criterion.design)}>Design v{criterion.design.version}</a>}
            </div>
          </div>
        </li>
      ))}</ol>
    </section>}
  </div>;
}

function DocList({ docs, empty, note }: { docs: Row[]; empty: string; note: string }) {
  return <div className="ticket-reader">
    <p className="ticket-note">{note}</p>
    {docs.length ? <ul className="ticket-list">{docs.map(doc => <li key={doc.id}>
      <a href={`#documents/${doc.id}`}>{doc.name}</a><small>{doc.document_type || "Document"} · revision {doc.revision}</small>
    </li>)}</ul> : <Empty>{empty}</Empty>}
  </div>;
}
