import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source=await readFile(new URL('../src/formActions.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
const {SubmissionGate,submitsMessage,sameTaskRequest,uncertainSubmission,guardDraftNavigation,PREVIEW_NAVIGATION}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
function deferred(){let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};}

test('a repeated submission cannot issue another request while the first waits',async()=>{
  const gate=new SubmissionGate(),response=deferred();let calls=0;
  const request=()=>{calls++;return response.promise;};
  const first=gate.run(request);
  assert.equal(gate.busy,true);
  assert.equal(await gate.run(request),undefined);
  assert.equal(calls,1);
  response.resolve('saved');
  assert.equal(await first,'saved');
  assert.equal(gate.busy,false);
  assert.equal(await gate.run(async()=>++calls),2);
});
test('a failed mutation propagates its error and permits an explicit retry',async()=>{
  const gate=new SubmissionGate(),response=deferred(),failure=new Error('Disconnected');
  const pending=gate.run(()=>response.promise);
  const rejected=assert.rejects(pending,error=>error===failure);
  response.reject(failure);await rejected;
  assert.equal(gate.busy,false);
  assert.equal(await gate.run(async()=>'retried'),'retried');
});
test('synchronous callback errors also release the gate',async()=>{
  const gate=new SubmissionGate();
  await assert.rejects(gate.run(()=>{throw new Error('Invalid state');}),/Invalid state/);
  assert.equal(gate.busy,false);
});
test('unrelated forms have independent gates',async()=>{
  const first=new SubmissionGate(),second=new SubmissionGate(),response=deferred();
  const pending=first.run(()=>response.promise);
  assert.equal(await second.run(async()=>'other form'),'other form');
  response.resolve();await pending;
});
test('Enter sends, Shift+Enter inserts text, and composing input is untouched',()=>{
  assert.equal(submitsMessage('Enter',false,false,13),true);
  for(const args of [['Enter',true,false,13],['Enter',false,true,13],['Enter',false,false,229],['a',false,false,65]])assert.equal(submitsMessage(...args),false);
});
test('dirty navigation waits for an explicit discard continuation',()=>{
  const target=new EventTarget();let resumed=0,prompt;
  const remove=guardDraftNavigation(target,()=>({dirty:true,busy:false}),resume=>{prompt=resume;});
  const event=Object.assign(new Event(PREVIEW_NAVIGATION,{cancelable:true}),{detail:{resume:()=>resumed++}});
  assert.equal(target.dispatchEvent(event),false);
  assert.equal(resumed,0);
  prompt();assert.equal(resumed,1);remove();
});
test('clean navigation proceeds, pending work blocks, and cleanup removes the guard',()=>{
  const target=new EventTarget();let busy=false,prompts=0;
  const remove=guardDraftNavigation(target,()=>({dirty:false,busy}),()=>prompts++);
  const event=()=>Object.assign(new Event(PREVIEW_NAVIGATION,{cancelable:true}),{detail:{resume:()=>{}}});
  assert.equal(target.dispatchEvent(event()),true);
  busy=true;assert.equal(target.dispatchEvent(event()),false);assert.equal(prompts,0);
  remove();assert.equal(target.dispatchEvent(event()),true);
});
test('uncertain task retries must keep the original submitted context',()=>{
  const request={message:'Fix Save',model:'model-a',mode:'Edit',ticketId:'ticket-a',roleId:'role-a'};
  assert.equal(sameTaskRequest(request,{...request}),true);
  for(const [field,value] of Object.entries({message:'Other task',model:'model-b',mode:'Read only',ticketId:'ticket-b',roleId:'role-b'}))assert.equal(sameTaskRequest(request,{...request,[field]:value}),false);
});
test('read-only retries ignore a ticket that is not part of the submitted request',()=>{
  const request={message:'Explain',model:'model-a',mode:'Read only',ticketId:'',roleId:''};
  assert.equal(sameTaskRequest(request,{...request,ticketId:'unused'}),true);
});
test('server and transport failures retain request identity for a safe retry',()=>{
  for(const status of [undefined,408,500,502,503,504])assert.equal(uncertainSubmission(status),true);
  for(const status of [400,401,403,404,409,422,429])assert.equal(uncertainSubmission(status),false);
});
