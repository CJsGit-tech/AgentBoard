import { Empty, Tag } from "../../Common";
import { currentReview, nameOf, type DesignReference, type Row, type Workspace } from "../../model";
import { Markdown } from "../documents/Markdown";
import { designHref, proofHref, resolveProof } from "./proof-links";
import "./ticket-reader.css";

export function TicketReader({ db, ticket, openRun }: { db: Workspace; ticket: Row; openRun: (run: Row) => void }) {
  const inProject = (row: Row) => row.project === ticket.project;
  const documents = db.documents.filter(inProject);
  const inputs = documents.filter(doc => ticket.documents?.includes(doc.id));
  const outputs = documents.filter(doc => ticket.output_documents?.includes(doc.id));
  const runs = db.runs.filter(run => inProject(run) && run.ticket === ticket.id);
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

  return <div className="ticket-reader">
    <dl><div><dt>Status</dt><dd><Tag value={ticket.status || "Unspecified"} /></dd></div>
      <div><dt>Milestone</dt><dd>{nameOf(db, "milestones", ticket.milestone)}</dd></div>
      <div><dt>Assigned role</dt><dd>{ticket.role ? nameOf(db, "roles", ticket.role) : "Unassigned"}</dd></div>
      {scopeReviewer && <div><dt>Scope checked by</dt><dd>{scopeReviewer}</dd></div>}</dl>
    {(designs.size > 0 || prerequisites.length > 0) && <section><h3>Design and prerequisites</h3><ul>
      {[...designs].map(([href, design]) => <li key={href}><a href={href}>{nameOf(db, "documents", design.document_id)} · Canvas v{design.version}</a></li>)}
      {prerequisites.map(row => <li key={row.id}><a href={`#tickets/${row.id}`}>{row.name}</a></li>)}
    </ul></section>}
    <section><h3>Work and acceptance criteria</h3>{text ? <Markdown text={text} resolveRecord={recordHref} /> : <Empty>No description recorded.</Empty>}
      {!!ticket.criteria?.length && <ol className="ticket-criteria">{ticket.criteria.map(criterion => {
        const design = criterion.design;
        const canOpenDesign = design && designs.has(designHref(design));
        const proofs = (criterion.evidence || []).map(proof => ({ proof, doc: resolveProof(db, ticket, proof) }));
        const verified = proofs.some(({ proof, doc }) => proof.status === "verified" && doc);
        return <li key={criterion.id}>
          <div className="ticket-criterion-head"><strong>{criterion.text}</strong><Tag value={verified ? "Verified" : "Unverified"} /></div>
          {design && (canOpenDesign ? <a href={designHref(design)}>Approved design · Canvas v{design.version}</a> : <p>Approved version unavailable.</p>)}
          {!!proofs.length && <ul>{proofs.map(({ proof, doc }, index) => <li key={`${proofHref(proof)}:${index}`}>
            {doc ? <a href={proofHref(proof)}>{proof.kind === "screenshot" ? proof.filename : doc.name}</a> : "Recorded proof unavailable"}
            {proof.status === "superseded" ? " · Superseded" : proof.status === "unverified" ? " · Unverified" : ""}
          </li>)}</ul>}
          {!proofs.length && <p>{criterion.evidence_required ? "Evidence required." : "No proof linked."}</p>}
        </li>;
      })}</ol>}
    </section>
    <section><h3>Context</h3>{inputs.length ? <ul>{inputs.map(doc => <li key={doc.id}><a href={`#documents/${doc.id}`}>{doc.name}</a></li>)}</ul> : <Empty>No context documents linked.</Empty>}</section>
    <section><h3>Outputs</h3>{outputs.length ? <ul>{outputs.map(doc => <li key={doc.id}><a href={`#documents/${doc.id}`}>{doc.name}</a></li>)}</ul> : <Empty>No output documents linked.</Empty>}</section>
    <section><h3>Runs</h3>{runs.length ? <ul>{runs.map(run => <li key={run.id}><button type="button" className="link" onClick={() => openRun(run)}>{run.name}</button> {run.status && <Tag value={run.status} />}{run.agent && <div><small>Reported agent · {run.agent}</small></div>}</li>)}</ul> : <Empty>No runs linked.</Empty>}</section>
  </div>;
}
