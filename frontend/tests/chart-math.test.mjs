import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';
const source=await readFile(new URL('../src/features/charts/chart-math.ts',import.meta.url),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
const m=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));

test('percent and target comparison handle empty data instead of inventing zero',()=>{
 assert.equal(m.percentOf(0,0),null);
 assert.equal(m.percentOf(44,53),83);
 assert.deepEqual(m.versusTarget(null,90),{met:null,gap:null});
 assert.deepEqual(m.versusTarget(83,90),{met:false,gap:-7});
 assert.deepEqual(m.versusTarget(1.1,4,true),{met:true,gap:2.9});
});

test('gauge clamps its fraction, draws no fill for zero and hides an edge target tick',()=>{
 const empty=m.gaugeGeometry(0,148,12,0.9);
 assert.equal(empty.fill,null); assert.ok(empty.tick); assert.ok(empty.track.startsWith('M'));
 assert.equal(m.gaugeGeometry(2,148).fraction,1);
 assert.equal(m.gaugeGeometry(Number.NaN,148).fraction,0);
 assert.equal(m.gaugeGeometry(0.5,148,12,1).tick,null);
});

test('pie handles empty, single-part and folded inputs',()=>{
 assert.deepEqual(m.pieSlices([],70),[]);
 const single=m.pieSlices([{name:'Only',value:5},{name:'Zero',value:0}],70);
 assert.equal(single.length,1); assert.equal(single[0].percent,100); assert.match(single[0].path,/a70,70/);
 const shares=m.pieSlices([{name:'A',value:27},{name:'B',value:9},{name:'C',value:9},{name:'D',value:8}],70);
 assert.deepEqual(shares.map(s=>s.percent),[51,17,17,15]);
 const folded=m.foldParts([{name:'a',value:5},{name:'b',value:4},{name:'c',value:3},{name:'d',value:2},{name:'e',value:1}]);
 assert.equal(folded.length,4); assert.deepEqual(folded[3],{name:'Other',value:3,folded:['d 2','e 1']});
});

test('axis and lines keep an axis for empty data and break on missing values',()=>{
 assert.deepEqual(m.axisTicks([]),{top:1,ticks:[0,1]});
 assert.equal(m.axisTicks([null,47,83],100).top,100);
 assert.deepEqual(m.axisTicks([17,16,29]),{top:30,ticks:[0,10,20,30]});
 assert.deepEqual(m.axisTicks([62,15,8,0]).ticks,[0,20,40,60,80]);
 assert.equal(m.linePath([null,null],i=>i,v=>v),'');
 assert.equal(m.linePath([5],i=>i*10,v=>v),'M0.0,5.0');
 assert.equal(m.linePath([1,null,3],i=>i,v=>v),'M0.0,1.0M2.0,3.0');
});

test('end labels never overlap and keep their input order',()=>{
 assert.deepEqual(m.spreadLabels([100,105,40]),[100,116,40]);
 assert.deepEqual(m.spreadLabels([]),[]);
});

test('burn-up steps start at the window, include single events and extend to the end',()=>{
 assert.deepEqual(m.burnupSteps([],0,10),[{at:0,scope:0,done:0},{at:10,scope:0,done:0}]);
 assert.deepEqual(m.burnupSteps([{created:2,done:5}],0,10),[{at:0,scope:0,done:0},{at:2,scope:1,done:0},{at:5,scope:1,done:1},{at:10,scope:1,done:1}]);
 assert.equal(m.nearestIndex(55,10,90,7),3); assert.equal(m.nearestIndex(0,10,90,1),0);
});

test('log scale, bead batches and median handle empty and single values',()=>{
 assert.equal(m.logPosition(1/12,1/12,16),0); assert.equal(m.logPosition(16,1/12,16),1); assert.equal(m.logPosition(100,1/12,16),1); assert.equal(m.logPosition(0,1/12,16),0);
 assert.deepEqual(m.beadGroups([]),[]);
 assert.deepEqual(m.beadGroups([11.81,11.8,11.79,0.5,-1,Number.NaN]),[{value:0.5,count:1},{value:11.8,count:3}]);
 assert.equal(m.medianOf([]),null); assert.equal(m.medianOf([3]),3); assert.equal(m.medianOf([1,2,3,10]),2.5);
});
