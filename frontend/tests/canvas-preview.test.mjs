import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../src/features/library/canvas-preview.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext}}).outputText;
const {canvasPreviewGeometry, matchesCanvasPublication, verifiedScreenCount} = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'));

test('criterion pins take precedence over historical descriptions and match an exact project and version', () => {
  const profile = {id: 'profile', project: 'project'};
  const ticket = {project: 'project', documents: ['profile'], description: '[Old design](#canvas/profile/2)', criteria: [{design: {document_id: 'profile', version: 1}}]};
  assert.equal(matchesCanvasPublication(ticket, profile, 1), true);
  assert.equal(matchesCanvasPublication(ticket, profile, 2), false);
  assert.equal(matchesCanvasPublication({...ticket, project: 'other'}, profile, 1), false);
});

test('legacy local Canvas URLs are eligible only with a same-project Context link and exact version', () => {
  const profile = {id: 'D-example', project: 'project'};
  const ticket = {project: 'project', documents: ['D-example'], description: '核准畫布 v1：http://127.0.0.1:8080/#canvas/D-example/11'};
  assert.equal(matchesCanvasPublication(ticket, profile, 11), true);
  assert.equal(matchesCanvasPublication(ticket, profile, 1), false);
  assert.equal(matchesCanvasPublication({...ticket, documents: []}, profile, 11), false);
  assert.equal(matchesCanvasPublication({...ticket, description: '[Unrelated](https://example.com/#canvas/D-example/11)'}, profile, 11), false);
});

test('opening fit preserves narrow breakpoints and actual size leaves the iframe unscaled', () => {
  const geometry = canvasPreviewGeometry(390, 588, true);
  assert.deepEqual(geometry, {width: '390px', height: '980px', scale: .6});
  assert.deepEqual(canvasPreviewGeometry(1200, 588, true), {width: '2000px', height: '980px', scale: .6});
  assert.deepEqual(canvasPreviewGeometry(390, 588, false), {width: '100%', height: '100%', scale: 1});
});

test('archived unknown counts stay unknown and verified metadata is shown as saved', () => {
  assert.equal(verifiedScreenCount(null), 'Not recorded');
  assert.equal(verifiedScreenCount(0), 'Not recorded');
  assert.equal(verifiedScreenCount(40), '40');
});
