import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../src/features/workspace/conditional-read.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext}}).outputText;
const {conditionalRead} = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'));
const path = 'workspace?project=p1';

test('unchanged polls reuse the same snapshot and never read the body', async t => {
  const cached = {path, etag: '"p1-1"', data: {tickets: []}};
  t.mock.method(globalThis, 'fetch', async (url, init) => {
    assert.equal(url, '/api/' + path);
    assert.equal(init.headers['If-None-Match'], cached.etag);
    assert.equal(init.cache, 'no-store');
    return {status: 304, json() { throw Error('304 has no body'); }};
  });
  assert.equal(await conditionalRead(path, cached), cached);
});

test('directory and project validators never cross scopes', async t => {
  const cached = {path: 'workspace?view=projects', etag: '"dir"', data: {}};
  t.mock.method(globalThis, 'fetch', async (_url, init) => {
    assert.equal(init.headers['If-None-Match'], undefined);
    return Response.json({tickets: ['t1']}, {headers: {etag: '"p1-2"'}});
  });
  const next = await conditionalRead(path, cached);
  assert.deepEqual(next, {path, etag: '"p1-2"', data: {tickets: ['t1']}});
});

test('a newer version replaces the prior snapshot and validator together', async t => {
  const cached = {path, etag: '"old"', data: {revision: 1}};
  t.mock.method(globalThis, 'fetch', async (_url, init) => {
    assert.equal(init.headers['If-None-Match'], '"old"');
    return Response.json({revision: 2}, {headers: {etag: '"new"'}});
  });
  assert.deepEqual(await conditionalRead(path, cached), {path, etag: '"new"', data: {revision: 2}});
  assert.equal(cached.data.revision, 1);
});

test('failed revalidation never confirms a cached write', async t => {
  const cached = {path, etag: '"old"', data: {}};
  t.mock.method(globalThis, 'fetch', async () => Response.json({detail: 'Unavailable'}, {status: 503}));
  await assert.rejects(conditionalRead(path, cached), {status: 503, message: 'Unavailable'});
});
