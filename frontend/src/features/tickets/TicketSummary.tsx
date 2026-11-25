import { type Row, type Workspace } from "../../model";
import { Icon, Tag } from "../../Common";
import "./tickets.css";
export function ticketRole(db: Workspace, ticket: Row) { return ticket.role ? db.roles.find(r=>r.id===ticket.role && r.project===ticket.project)?.name || "Role unavailable" : "No role set"; }
export function ticketMilestone(db: Workspace, ticket: Row) { return ticket.milestone ? db.milestones.find(m=>m.id===ticket.milestone && m.project===ticket.project)?.name || "Milestone unavailable" : "No milestone"; }
export function TicketSummary({db,ticket,open,status=false}:{db:Workspace;ticket:Row;open?:(ticket:Row)=>void;status?:boolean}) {
 return <div className="ticket-summary"><div className="ticket-context"><Icon page={ticket.work_type==="BUG"?"bug":"build"}/><span>{ticket.work_type==="BUILD"?"Build":ticket.work_type==="BUG"?"Bug":"Unclassified"}</span><span>·</span><span>{ticketMilestone(db,ticket)}</span></div>
  {open?<button data-drag-title className="ticket-name" onClick={e=>{e.stopPropagation();open(ticket);}}>{ticket.name}</button>:<strong className="ticket-name">{ticket.name}</strong>}
  <dl className="ticket-responsibility"><div><dt>Assigned to</dt><dd>Not recorded</dd></div><div><dt>Role</dt><dd>{ticketRole(db,ticket)}</dd></div></dl>{status&&<Tag value={ticket.status||"Unspecified"}/>}</div>;
}
