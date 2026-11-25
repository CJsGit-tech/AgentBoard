export type TicketState = {id:string;status?:string};
export type StatusEvent = {id:string;time:string;kind:string;record:string;changes:[string,unknown,unknown][]};
export type DeliveryPoint = {time:number;done:number;total:number};
const states=new Set(['Planned','In progress','Blocked','Done']);

/** Replay the current ticket cohort, counting states rather than completion events. */
export function deliveryHistory(tickets:TicketState[],activity:StatusEvent[]) {
  const ids=new Set(tickets.map(t=>t.id));
  const events=activity.filter(a=>a.kind==='tickets'&&ids.has(a.record)&&a.changes.some(c=>c[0]==='status'))
    .map(a=>({...a,at:Date.parse(a.time)})).sort((a,b)=>a.at-b.at||Number(a.id)-Number(b.id));
  if(events.some(e=>!Number.isFinite(e.at)))throw new Error('Ticket history has an invalid timestamp.');
  const current=new Map<string,string>();
  const points:DeliveryPoint[]=[];
  for(const event of events) {
    const status=event.changes.find(c=>c[0]==='status')![2];
    if(status===null)current.delete(event.record);
    else if(typeof status==='string'&&states.has(status))current.set(event.record,status);
    else throw new Error('Ticket history has an unsupported status.');
    const point={time:event.at,done:[...current.values()].filter(s=>s==='Done').length,total:current.size};
    if(points.at(-1)?.time===point.time)points[points.length-1]=point;else points.push(point);
  }
  const covered=tickets.filter(t=>current.has(t.id)).length;
  const checkpoints:DeliveryPoint[]=[];
  if(points.length) {
    const first=points[0].time,last=points.at(-1)!.time;
    const times=[first];
    for(let time=Math.ceil((first+1)/3600000)*3600000;time<last;time+=3600000)times.push(time);
    if(last!==first)times.push(last);
    let index=0;
    for(const time of times){while(index+1<points.length&&points[index+1].time<=time)index++;checkpoints.push({...points[index],time});}
  }
  return {points,checkpoints,covered,complete:covered===tickets.length&&tickets.length>0,
    matchesCurrent:tickets.every(t=>current.get(t.id)===t.status)};
}

export function statusCounts(tickets:TicketState[]) {
  return ['Planned','In progress','Blocked','Done'].map(status=>({status,count:tickets.filter(t=>t.status===status).length}));
}

export function stepPath(points:DeliveryPoint[],field:'done'|'total',width=640,height=204) {
  if(!points.length)return '';
  const start=points[0].time,span=Math.max(1,points.at(-1)!.time-start);
  const max=Math.max(1,...points.map(p=>p.total));
  const x=(p:DeliveryPoint)=>38+(p.time-start)/span*(width-54);
  const y=(p:DeliveryPoint)=>height-30-p[field]/max*(height-48);
  return points.map((p,i)=>i?`H${x(p).toFixed(2)}V${y(p).toFixed(2)}`:`M${x(p).toFixed(2)},${y(p).toFixed(2)}`).join('');
}

type Report={id:string;name:string;status?:string;agent?:string;ticket?:string;updated?:string};
type Managed={id:string;name?:string;status:string;board_run_id:string|null;ticket_id:string|null;updated_at:string;role_name?:string|null};
type LinkedTicket={id:string;name:string;status?:string;role?:string};
export type WorkloadTask={id:string;name:string;agent:string;status:string;updated:string|null;boardRunId:string|null;managedRunId:string|null;ticketId:string|null;ticketName:string|null;ticketStatus:string|null;role:string|null;roleSource:'Run role'|'Ticket role'|null};
const runStates=new Set(['Queued','Running','Waiting for input','Blocked','Completed','Failed','Cancelled']);
const activeStates=new Set(['Running','Queued','Waiting for input','Blocked']);

/** Managed execution status wins over its linked board report; each execution is counted once. */
export function agentWorkload(reports:Report[],managed:Managed[],tickets:LinkedTicket[],roles:{id:string;name:string}[]) {
  const tasks=new Map<string,WorkloadTask>();
  const metadata=(ticketId:string|null,roleName?:string|null)=>{
    const ticket=tickets.find(t=>t.id===ticketId);
    const ticketRole=roles.find(r=>r.id===ticket?.role)?.name;
    return {ticketId,ticketName:ticket?.name||null,ticketStatus:ticket?.status||null,
      role:roleName||ticketRole||null,roleSource:roleName?'Run role' as const:ticketRole?'Ticket role' as const:null};
  };
  for(const r of reports)tasks.set(r.id,{id:r.id,name:r.name,agent:r.agent?.trim()||'Agent not recorded',status:r.status||'Not recorded',updated:r.updated||null,boardRunId:r.id,managedRunId:null,...metadata(r.ticket||null)});
  for(const r of managed) {
    const key=r.board_run_id||r.id,existing=tasks.get(key);
    tasks.set(key,{id:key,name:existing?.name||r.name||'Untitled task',agent:existing?.agent==='Agent not recorded'?'InApp Assistant':existing?.agent||'InApp Assistant',status:r.status,updated:r.updated_at,boardRunId:r.board_run_id,managedRunId:r.id,...metadata(r.ticket_id,r.role_name)});
  }
  for(const task of tasks.values()) {
    if(!runStates.has(task.status)&&task.status!=='Not recorded')throw new Error('Unknown run status in workload.');
    if(task.updated&&!Number.isFinite(Date.parse(task.updated)))throw new Error('Invalid workload report timestamp.');
  }
  const all=[...tasks.values()];
  const count=(items:WorkloadTask[],status:string)=>items.filter(t=>t.status===status).length;
  const agents=[...new Set(all.map(t=>t.agent))].map(agent=>{
    const items=all.filter(t=>t.agent===agent);
    const active=items.filter(t=>activeStates.has(t.status)).sort((a,b)=>{
      const rank=['Running','Queued','Waiting for input','Blocked'];
      return rank.indexOf(a.status)-rank.indexOf(b.status)||(b.updated?Date.parse(b.updated):0)-(a.updated?Date.parse(a.updated):0);
    });
    const running=count(items,'Running'),queued=count(items,'Queued'),waiting=count(items,'Waiting for input')+count(items,'Blocked');
    const latest=items.filter(t=>t.updated).sort((a,b)=>Date.parse(b.updated!)-Date.parse(a.updated!))[0];
    return {agent,active,running,queued,waiting,completed:count(items,'Completed'),total:items.length,lastReport:latest?.updated||null,state:running?'Running':queued?'Queued':waiting?'Waiting':items.some(t=>t.status==='Not recorded')?'Unknown':'Idle'};
  }).sort((a,b)=>b.running-a.running||b.active.length-a.active.length||a.agent.localeCompare(b.agent));
  return {agents,tasks:all,running:count(all,'Running'),queued:count(all,'Queued'),waiting:count(all,'Waiting for input')+count(all,'Blocked'),completed:count(all,'Completed'),failed:count(all,'Failed'),total:all.length};
}
export type Workload=ReturnType<typeof agentWorkload>;
