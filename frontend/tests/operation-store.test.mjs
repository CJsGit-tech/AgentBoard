import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';
const source=await readFile(new URL('../src/features/operations/operation-store.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
const {OperationStore}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
const config=(extra={})=>({resources:['project:a'],label:'Saving ticket',completed:'Saved',write:async()=>({revision:2}),sync:async()=>{},...extra});
test('the lock spans writing and sync, including competing entry points',async()=>{
 const store=new OperationStore(),write=deferred(),read=deferred();let calls=0;
 const run=()=>store.run(config({write:()=>{calls++;return write.promise;},sync:()=>read.promise}));
 const first=run();assert.equal(store.getSnapshot()[0].phase,'writing');assert.equal((await run()).state,'blocked');
 write.resolve({revision:2});await Promise.resolve();await Promise.resolve();assert.equal(store.getSnapshot()[0].phase,'syncing');assert.equal((await run()).state,'blocked');assert.equal(calls,1);
 read.resolve();assert.equal((await first).state,'confirmed');assert.equal(store.pending,false);
});
test('failed refresh keeps a lock and retries only reads after successful save',async()=>{
 const store=new OperationStore();let writes=0,reads=0;
 const result=await store.run(config({write:async()=>++writes,sync:async()=>{if(++reads===1)throw Error('503');}}));
 assert.equal(result.state,'sync-failed');assert.match(store.getSnapshot()[0].message,/Saved; refresh failed/);
 const id=store.getSnapshot()[0].id;store.dismiss(id);assert.equal(store.pending,true);await store.retry(id);assert.equal(writes,1);assert.equal(reads,2);assert.equal(store.pending,false);
});
test('lost response reconciles saved state without repeating the write',async()=>{
 const store=new OperationStore();let writes=0,reads=0;
 const result=await store.run(config({write:async()=>{writes++;throw Error('lost');},reconcile:async()=>{reads++;return {revision:2};}}));
 assert.equal(result.state,'confirmed');assert.equal(writes,1);assert.equal(reads,1);assert.equal(store.pending,false);
});
test('an uncertain result remains protected and provides read-only repair',async()=>{
 const store=new OperationStore();let writes=0,reads=0;
 const run=()=>store.run(config({write:async()=>{writes++;throw Error('lost');},reconcile:async()=>{reads++;throw Error('unconfirmed');}}));
 assert.equal((await run()).state,'uncertain');const id=store.getSnapshot()[0].id;assert.equal((await run()).state,'blocked');await store.retry(id);assert.equal(writes,1);assert.equal(reads,2);assert.equal(store.getSnapshot()[0].phase,'uncertain');
});
test('definite validation and revision errors unlock while retaining the error',async()=>{
 for(const status of [400,404,409,422]){const store=new OperationStore(),error=Object.assign(Error('Rejected'),{status});await assert.rejects(store.run(config({write:async()=>{throw error;}})),e=>e===error);assert.equal(store.pending,false);assert.equal(store.getSnapshot()[0].phase,'failed');store.dismiss(store.getSnapshot()[0].id);assert.deepEqual(store.getSnapshot(),[]);}
});
test('unrelated project can complete without releasing the first project lock',async()=>{
 const store=new OperationStore(),read=deferred();const a=store.run(config({sync:()=>read.promise}));await Promise.resolve();await Promise.resolve();assert.equal((await store.run(config({resources:['project:b']}))).state,'confirmed');assert.equal(store.locked(['project:a']),true);read.resolve();await a;
});
test('repeated Retry sync while its read waits does not start another read',async()=>{
 const store=new OperationStore(),read=deferred();let reads=0;await store.run(config({sync:async()=>{if(++reads===1)throw Error('failed');await read.promise;}}));const id=store.getSnapshot()[0].id;const retry=store.retry(id);await store.retry(id);assert.equal(reads,2);read.resolve();await retry;
});
test('read freshness epoch advances on write start and its confirmed response',async()=>{
 const store=new OperationStore(),write=deferred();let notifications=0;const stop=store.subscribe(()=>notifications++);const pending=store.run(config({write:()=>write.promise}));const epoch=store.epoch;assert.ok(epoch>0);write.resolve(2);await pending;assert.ok(store.epoch>epoch);assert.ok(notifications>=3);stop();
});
test('success focus/reveal runs once after a failed sync is repaired, not before',async()=>{
 const store=new OperationStore();let reads=0,settled=0;await store.run(config({sync:async()=>{if(++reads===1)throw Error('sync failed');},settled:()=>settled++}));assert.equal(settled,0);await store.retry(store.getSnapshot()[0].id);assert.equal(settled,1);
});
