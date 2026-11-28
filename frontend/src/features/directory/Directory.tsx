import type { WorkspaceRefresh } from "../../model";
import { useRef, useState } from "react";
import { Button, Drawer } from "@mantine/core";
import { type Editor, type Row, type Workspace, done, percent } from "../../model";
import { Meter } from "../../Dashboard";
import { Empty } from "../../Common";
import { RecordEditor } from "../../RecordEditor";
import { TicketSummary } from "../tickets/TicketSummary";
import { ticketsForMilestone } from "../tickets/milestone";
import "./directory.css";
import { RoleBars, type RoleLoad } from "../charts/RoleBars";
import { MeterBar } from "../charts/MeterBar";
import { ChartCard, DataTable } from "../charts/BI";
import { MilestoneTimeline, LeadBeads, type MilestoneSpan } from "../charts/MilestoneCharts";
import { beadGroups, medianOf } from "../charts/chart-math";
import { StatusBar } from "../charts/primitives";
export function Directory({kind,db,rows,edit,milestone,refresh}:{kind:"roles"|"milestones";db:Workspace;rows:Row[];edit:(editor:Editor)=>void;milestone:(id:string)=>void;refresh?:WorkspaceRefresh}) {
 const [selected,setSelected]=useState<Row|null>(null),[linked,showLinked]=useState(false);
 const opener=useRef<HTMLButtonElement|null>(null);
 const projectTickets=(row:Row)=>db.tickets.filter(ticket=>ticket.project===row.project);
 const related=(row:Row)=>kind==="milestones"?ticketsForMilestone(db.tickets,row):db.tickets.filter(ticket=>ticket.project===row.project&&ticket.role===row.id);
 function select(row:Row,button:HTMLButtonElement) {if(!window.dispatchEvent(new Event("agentboard:before-navigate",{cancelable:true})))return;opener.current=button;setSelected(row);showLinked(false);}
 function close(){setSelected(null);showLinked(false);requestAnimationFrame(()=>opener.current?.focus());}
 if(!rows.length)return <Empty>No matching records.</Empty>;
 const loads:RoleLoad[]=kind==="roles"?rows.map(row=>{const t=related(row);return {role:row.name,build:t.filter(x=>x.work_type==="BUILD").length,bug:t.filter(x=>x.work_type==="BUG").length,other:t.filter(x=>x.work_type!=="BUILD"&&x.work_type!=="BUG").length};}):[];
 const linkedTotal=loads.reduce((n,r)=>n+r.build+r.bug+r.other,0),top=[...loads].sort((a,b)=>(b.build+b.bug+b.other)-(a.build+a.bug+a.other))[0],idle=loads.filter(r=>!(r.build+r.bug+r.other)).length;
 const leadHours=(t:Row)=>(Date.parse(t.updated_at||"")-Date.parse(t.created_at||""))/3600000;
 const spans:MilestoneSpan[]=kind==="milestones"?rows.map(row=>{const t=related(row);const d=t.filter(x=>x.status==="Done");return {id:row.id,name:row.name,start:Math.min(...t.map(x=>Date.parse(x.created_at||""))),end:Math.max(...t.map(x=>Date.parse(x.updated_at||x.created_at||""))),done:d.length,total:t.length,median:medianOf(d.map(leadHours))};}).sort((a,b)=>a.start-b.start):[];
 const allDone=spans.flatMap(sp=>related(rows.find(r=>r.id===sp.id)!).filter(x=>x.status==="Done").map(leadHours)).filter(Number.isFinite);
 const overallMedian=medianOf(allDone),biggestBatch=spans.map(sp=>({sp,b:[...beadGroups(related(rows.find(r=>r.id===sp.id)!).filter(x=>x.status==="Done").map(leadHours))].sort((a,b)=>b.count-a.count)[0]})).filter(x=>x.b).sort((a,b)=>b.b.count-a.b.count)[0];
 const fmtH=(h:number)=>h<1?`${Math.round(h*60)} min`:`${h.toFixed(h<10?1:0)} h`;
 return <>{kind==="milestones"&&spans.some(sp=>sp.total)&&<div className="milestone-charts">
   <ChartCard title="Timeline" insight="Each bar runs from the first ticket filed to the last update; the fill shows how much is done."
     table={<DataTable head={["Milestone","First ticket","Last update","Done"]} rows={spans.filter(sp=>sp.total).map(sp=>[sp.name,new Date(sp.start).toLocaleString(),new Date(sp.end).toLocaleString(),`${sp.done}/${sp.total}`])}/>}>
     <MilestoneTimeline spans={spans} onOpen={id=>milestone(id)}/>
   </ChartCard>
   <ChartCard title="Time from filing to last update" insight={overallMedian===null?"No done tickets yet.":`Half of done tickets reached their last update within ${fmtH(overallMedian)}.${biggestBatch&&biggestBatch.b.count>1?` The largest batch: ${biggestBatch.b.count} ${biggestBatch.sp.name} tickets at ${fmtH(biggestBatch.b.value)}.`:""}`}
     table={<DataTable head={["Milestone","Done tickets","Median","Longest"]} rows={spans.filter(sp=>sp.done).map(sp=>{const h=related(rows.find(r=>r.id===sp.id)!).filter(x=>x.status==="Done").map(leadHours).filter(Number.isFinite);return [sp.name,h.length,sp.median===null?"–":fmtH(sp.median),h.length?fmtH(Math.max(...h)):"–"];})}/>}>
     <LeadBeads rows={spans.map(sp=>({name:sp.name,hours:related(rows.find(r=>r.id===sp.id)!).filter(x=>x.status==="Done").map(leadHours).filter(Number.isFinite)}))}/>
     <p className="cv-note">Each bead is one or more tickets that reached their last update after the same time; the number is how many. The dark tick is the median. Log scale. Tickets have no completion time, so this is time to last update.</p>
   </ChartCard>
 </div>}{kind==="roles"&&linkedTotal>0&&top&&<div className="role-chart"><RoleBars rows={loads} title="Who carries the work" insight={`${top.role} carries ${top.build+top.bug+top.other} of ${linkedTotal} linked tickets.${idle?` ${idle} ${idle===1?"role has":"roles have"} none.`:""}`}/></div>}
 <div className={"directory-layout"+(selected?" is-expanded":"")}><div className="directory-cards">{rows.map(row=>{const tickets=related(row);return <article className="directory-card" key={row.id} data-selected={selected?.id===row.id||undefined}>
   <h2><button className="plain" aria-pressed={selected?.id===row.id} onClick={event=>kind==="roles"?select(row,event.currentTarget):edit({kind,row})}>{row.name}</button></h2>
   {kind==="roles"?<><p className="role-charter">{row.instructions?.trim()||"No instructions recorded"}</p>
     <div className="role-share"><MeterBar value={tickets.length} total={projectTickets(row).length} label={`${row.name} share of project tickets`}/><span><b>{tickets.length}</b> linked {tickets.length===1?"ticket":"tickets"} · {projectTickets(row).length?Math.round(100*tickets.length/projectTickets(row).length):0}%</span></div></>:<><p>{tickets.length?`${done(tickets)} of ${tickets.length} tickets done · ${percent(tickets)}%`:"Progress pending"}</p><StatusBar counts={Object.fromEntries(["Done","In progress","Blocked","Planned"].map(st=>[st,tickets.filter(t=>t.status===st).length]))} label={`${row.name} ticket status`}/>
   <small className="milestone-median">{(()=>{const m=medianOf(tickets.filter(t=>t.status==="Done").map(leadHours));return m===null?"No done tickets yet":`Median time to last update ${fmtH(m)}`;})()}</small><button className="link" onClick={()=>milestone(row.id)}>View {tickets.length} tickets →</button></>}
 </article>;})}</div>
 {selected&&<section className="directory-detail"><header><h2>{selected.name}</h2><button className="link" onClick={()=>showLinked(true)}>View linked tickets ({related(selected).length})</button><Button variant="default" size="xs" onClick={()=>{if(window.dispatchEvent(new Event("agentboard:before-navigate",{cancelable:true})))close();}}>Close details</Button></header>
 <RecordEditor key={selected.id} inline db={db} editor={{kind:"roles",row:selected}} scope={selected.project||""} close={close} open={edit} refresh={refresh||(async()=>{})}/>
 <Drawer opened={linked} onClose={()=>showLinked(false)} title={"Linked tickets · "+selected.name} position="right" size="min(520px,95vw)" closeButtonProps={{"aria-label":"Close linked tickets"}}>
 {related(selected).map(ticket=><div className="log" key={ticket.id}><TicketSummary db={db} ticket={ticket} open={row=>edit({kind:"tickets",row})} metadata="none" status/></div>)}{!related(selected).length&&<Empty>No linked tickets.</Empty>}
 </Drawer></section>}
 </div></>;
}
