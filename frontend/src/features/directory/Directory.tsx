import type { WorkspaceRefresh } from "../../model";
import { useRef, useState } from "react";
import { Button, Drawer } from "@mantine/core";
import { type Editor, type Row, type Workspace, done, percent } from "../../model";
import { Meter } from "../../Dashboard";
import { Empty } from "../../Common";
import { RecordEditor } from "../../RecordEditor";
import { TicketSummary } from "../tickets/TicketSummary";
import "./directory.css";
export function Directory({kind,db,rows,edit,milestone,refresh}:{kind:"roles"|"milestones";db:Workspace;rows:Row[];edit:(editor:Editor)=>void;milestone:(id:string)=>void;refresh?:WorkspaceRefresh}) {
 const [selected,setSelected]=useState<Row|null>(null),[linked,showLinked]=useState(false);
 const opener=useRef<HTMLButtonElement|null>(null);
 const related=(row:Row)=>db.tickets.filter(t=>kind==="roles"?t.role===row.id:t.milestone===row.id);
 function select(row:Row,button:HTMLButtonElement) {if(!window.dispatchEvent(new Event("agentboard:before-navigate",{cancelable:true})))return;opener.current=button;setSelected(row);showLinked(false);}
 function close(){setSelected(null);showLinked(false);requestAnimationFrame(()=>opener.current?.focus());}
 if(!rows.length)return <Empty>No matching records.</Empty>;
 return <div className={"directory-layout"+(selected?" is-expanded":"")}><div className="directory-cards">{rows.map(row=>{const tickets=related(row);return <article className="directory-card" key={row.id} data-selected={selected?.id===row.id||undefined}>
   <h2><button className="plain" aria-pressed={selected?.id===row.id} onClick={event=>kind==="roles"?select(row,event.currentTarget):edit({kind,row})}>{row.name}</button></h2>
   {kind==="roles"?<><p>{row.instructions?.trim()?"Instructions saved":"No instructions recorded"}</p><span>{tickets.length} linked {tickets.length===1?"ticket":"tickets"}</span></>:<><p>{tickets.length?`${done(tickets)} of ${tickets.length} tickets done · ${percent(tickets)}%`:"Progress pending"}</p><Meter tickets={tickets}/><button className="link" onClick={()=>milestone(row.id)}>View {tickets.length} tickets →</button></>}
 </article>;})}</div>
 {selected&&<section className="directory-detail"><header><h2>{selected.name}</h2><button className="link" onClick={()=>showLinked(true)}>View linked tickets ({related(selected).length})</button><Button variant="default" size="xs" onClick={()=>{if(window.dispatchEvent(new Event("agentboard:before-navigate",{cancelable:true})))close();}}>Close details</Button></header>
 <RecordEditor key={selected.id} inline db={db} editor={{kind:"roles",row:selected}} scope={selected.project||""} close={close} open={edit} refresh={refresh||(async()=>{})}/>
 <Drawer opened={linked} onClose={()=>showLinked(false)} title={"Linked tickets · "+selected.name} position="right" size="min(520px,95vw)" closeButtonProps={{"aria-label":"Close linked tickets"}}>
 {related(selected).map(ticket=><div className="log" key={ticket.id}><TicketSummary db={db} ticket={ticket} open={row=>edit({kind:"tickets",row})} status/></div>)}{!related(selected).length&&<Empty>No linked tickets.</Empty>}
 </Drawer></section>}
 </div>;
}
