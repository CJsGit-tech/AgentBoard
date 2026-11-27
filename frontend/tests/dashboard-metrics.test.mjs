import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';
const source=await readFile(new URL('../src/features/dashboard/metrics.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
const {deliveryHistory,agentWorkload}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const event=(id,status,time)=>({id:String(id),time:`2026-11-25T00:0${time}:00Z`,kind:'tickets',record:'a',changes:[['status',null,status]]});
test('recorded delivery counts current states, including reopened work',()=>{
 const history=deliveryHistory([{id:'a',status:'Blocked'}],[event(1,'Planned',0),event(2,'Done',1),event(3,'Done',2),event(4,'Blocked',3)]);
 assert.deepEqual(history.points.map(p=>p.done),[0,1,1,0]);assert.equal(history.points.at(-1).total,1);assert.equal(history.matchesCurrent,true);
});
test('missing history stays visibly incomplete rather than inventing a baseline',()=>{
 const history=deliveryHistory([{id:'a',status:'Done'},{id:'b',status:'Planned'}],[event(1,'Done',0)]);
 assert.equal(history.covered,1);assert.equal(history.complete,false);assert.equal(history.matchesCurrent,false);
 assert.equal(deliveryHistory([],[]).complete,false);
});
test('recorded steps expose source status transitions, same-time events, and exact timestamps',()=>{
 const first={...event(1,'Planned',0),action:'Created'};
 const completion={...event(2,'Done',2),changes:[['status','Planned','Done']]};
 const sameTime={...event(3,'Blocked',2),record:'b',changes:[['status','In progress','Blocked']]};
 const noChange=event(4,'Done',3);
 const unrelated={...event(5,'Done',2),record:'other'};
 const history=deliveryHistory([{id:'a',status:'Done'},{id:'b',status:'Blocked'}],[noChange,sameTime,completion,first,unrelated]);
 assert.equal(history.checkpoints[0].time,Date.parse(first.time));
 assert.deepEqual(history.checkpoints[0].changes,[{id:'1',ticketId:'a',from:null,to:'Planned',created:true}]);
 assert.equal(history.checkpoints[1].time,Date.parse(completion.time));
 assert.deepEqual(history.checkpoints[1].changes.map(({ticketId,from,to})=>[ticketId,from,to]),[
  ['a','Planned','Done'],['b','In progress','Blocked']
 ]);
 assert.deepEqual(history.checkpoints[2].changes,[]);
 assert.equal(history.matchesCurrent,true);
});
test('unreadable status events are counted without hiding the available history',()=>{
 const invalidTime={...event(2,'Done',1),time:'invalid'};
 const invalidStatus=event(3,'unsupported',2);
 const history=deliveryHistory([{id:'a',status:'Done'}],[event(1,'Planned',0),invalidTime,invalidStatus]);
 assert.equal(history.unavailable,2);
 assert.deepEqual(history.points.map(point=>point.done),[0]);
 assert.equal(history.matchesCurrent,false);
});
test('completed reports do not become active tasks or acquire guessed ownership',()=>{
 const workload=agentWorkload([{id:'r',name:'Report',status:'Completed',agent:'Codex'}],[],[],[]);
 assert.equal(workload.running,0);assert.equal(workload.agents[0].state,'Idle');assert.equal(workload.tasks[0].role,null);
});
test('managed execution replaces its board report exactly once',()=>{
 const workload=agentWorkload([{id:'r',name:'Report',status:'Running',agent:'InApp Assistant'}],[{id:'managed',board_run_id:'r',status:'Queued',ticket_id:null,updated_at:'2026-11-25T00:00:00Z'}],[],[]);
 assert.equal(workload.total,1);assert.equal(workload.running,0);assert.equal(workload.queued,1);
});
