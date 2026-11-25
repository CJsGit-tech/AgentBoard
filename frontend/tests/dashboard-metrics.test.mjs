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
test('completed reports do not become active tasks or acquire guessed ownership',()=>{
 const workload=agentWorkload([{id:'r',name:'Report',status:'Completed',agent:'Codex'}],[],[],[]);
 assert.equal(workload.running,0);assert.equal(workload.agents[0].state,'Idle');assert.equal(workload.tasks[0].role,null);
});
test('managed execution replaces its board report exactly once',()=>{
 const workload=agentWorkload([{id:'r',name:'Report',status:'Running',agent:'InApp Assistant'}],[{id:'managed',board_run_id:'r',status:'Queued',ticket_id:null,updated_at:'2026-11-25T00:00:00Z'}],[],[]);
 assert.equal(workload.total,1);assert.equal(workload.running,0);assert.equal(workload.queued,1);
});
