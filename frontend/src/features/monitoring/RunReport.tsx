import { Empty, Tag } from "../../Common";
import { Markdown } from "../documents/Markdown";
import { stamp, type Change, type Row, type Workspace } from "../../model";
import { runReportNotes } from "./report-view";

export function RunReport({ db, run, history, openTicket }: {
  db: Workspace;
  run: Row;
  history: Change[];
  openTicket: (ticket: Row) => void;
}) {
  const ticket = db.tickets.find(row => row.id === run.ticket && row.project === run.project);
  const documents = ticket?.output_documents || [];
  const { latest, initial, unchanged } = runReportNotes(run, history);

  return <div className="run-report">
    <h3>{run.name}</h3>
    <dl className="run-report-facts">
      <div><dt>Run status</dt><dd><Tag value={run.status || "Unspecified"} /></dd></div>
      <div><dt>Ticket status</dt><dd>{ticket ? <Tag value={ticket.status || "Unspecified"} /> : run.ticket ? "Unavailable" : "No linked ticket"}</dd></div>
      <div><dt>Agent</dt><dd>{run.agent || "Not recorded"}</dd></div>
      <div><dt>Run mode</dt><dd>{run.mode || "Not recorded"}</dd></div>
      <div><dt>Last report</dt><dd>{stamp(run.updated)}</dd></div>
    </dl>
    <section>
      <h4>Linked ticket and evidence</h4>
      {ticket ? <button type="button" className="link" onClick={() => openTicket(ticket)}>{ticket.name}</button>
        : <Empty>{run.ticket ? "The linked ticket is unavailable." : "This run has no linked ticket."}</Empty>}
      {documents.length ? <ul>{documents.map(id => {
        const document = db.documents.find(row => row.id === id && row.project === run.project);
        return <li key={id}>{document ? <a className="link" href={`#documents/${encodeURIComponent(document.id)}`}>{document.name}</a> : "Linked output document unavailable"}</li>;
      })}</ul> : ticket && <Empty>No output evidence is linked to the ticket.</Empty>}
      {run.assistant_run_id ? <a className="link" href={`#project/${encodeURIComponent(run.project || "")}/assistant?run=${encodeURIComponent(run.assistant_run_id)}`}>View Assistant checks and run details</a>
        : <p className="run-report-source">External run checks are available when recorded in the report or linked evidence.</p>}
    </section>
    <section>
      <h4>Latest report</h4>
      {unchanged ? <>
        <p>The run status changed, but the report text is unchanged from when the run started.</p>
        <details><summary>Initial report</summary><Markdown text={latest} /></details>
      </> : latest ? <Markdown text={latest} /> : <Empty>No report text was recorded.</Empty>}
      {initial && <details><summary>Initial report</summary><Markdown text={initial} /></details>}
    </section>
  </div>;
}
