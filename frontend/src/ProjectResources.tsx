import { useState } from "react";
import { projectTags, type Row, type Workspace } from "./model";

const coreDocuments = [
  { title: "Product Brief", type: "product-vision", titles: ["product brief", "product vision"] },
  { title: "User Experiences", type: "user-story", titles: ["user experiences"] },
  { title: "Technical Stack", type: "architecture-topic", titles: ["technical stack", "tech stack"] },
  { title: "Design Profile", type: "design-topic", titles: ["design profile"] },
];
const defaultRoles = ["Product Manager", "Solution Architect", "Product Designer", "Frontend Programmer", "Backend Programmer", "Code Reviewer"];

export function ProjectResources({ db, project }: { db: Workspace; project: string }) {
  const [tag, setTag] = useState("");
  const documents = db.documents.filter(row => row.project === project);
  const roles = db.roles.filter(row => row.project === project);
  const missing = defaultRoles.filter(name => !roles.some(row => row.name.trim().toLowerCase() === name.toLowerCase()));
  const catalog = projectTags(documents);
  const entry = catalog.find(item => item.id === tag);
  const tickets = db.tickets.filter(row => row.project === project);
  const related = (rows: Row[], kind: "documents" | "tickets") => rows.filter(row => row.tags?.includes(tag))
    .map(row => <li key={row.id}><a href={`#${kind}/${row.id}`}>{row.name}</a> <small>{kind === "tickets" ? "Ticket" : row.document_type === "screen-inventory" ? "Visuals" : "Document"}</small></li>);
  const matches = tag ? [...related(documents, "documents"), ...related(tickets, "tickets")] : [];
  return <section className="project-resources">
    <h2>Project setup</h2>
    <dl>{coreDocuments.map(core => {
      const rows = documents.filter(row => row.document_type === core.type && core.titles.includes(row.name.trim().toLowerCase()));
      return <div key={core.title}><dt>{core.title}</dt><dd>{rows.length ? rows.map(row =>
        <a key={row.id} href={`#documents/${row.id}`}>{rows.length === 1 ? "Open document" : `${row.name} · Revision ${row.revision}`}</a>) : "Missing"}</dd></div>;
    })}</dl>
    <details><summary>Default roles · {6 - missing.length} of 6 ready</summary>
      {missing.length > 0 && <p>Missing: {missing.join(", ")}.</p>}
      <ul>{roles.map(row => <li key={row.id}><a href={`#roles/${row.id}`}>{row.name}</a></li>)}</ul>
    </details>
    {catalog.length > 0 && <details><summary>Find related work by tag</summary>
      <label>Project tag <select value={tag} onChange={event => setTag(event.target.value)}>
        <option value="">Choose a tag</option>
        {catalog.map(item => <option value={item.id} key={item.id}>{item.label}{item.state === "Retired" ? " (retired)" : ""}</option>)}
      </select></label>
      {entry && <><p>{entry.meaning || entry.id}</p>{matches.length ? <ul>{matches}</ul> : <p>No records use this tag yet.</p>}</>}
    </details>}
  </section>;
}
