import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import ts from 'typescript';

const source = await readFile(new URL('../src/features/monitoring/report-view.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext}}).outputText;
const {reviewDecision, runReportNotes} = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'));

test('a review summary displays the actual resulting state and saved rationale', () => {
  const assessment = {changes: [['Review result', 'Pending', 'Needs updates'], ['Rationale', '', 'Refresh the evidence.']]};
  assert.deepEqual(reviewDecision(assessment), {result: 'Needs updates', rationale: 'Refresh the evidence.', decidedBy: ''});
  const decision = {changes: [['Review result', 'Awaiting confirmation', 'Confirmed'], ['Decision by', null, 'User via Codex'], ['Scope decision', null, 'I confirm.']]};
  assert.deepEqual(reviewDecision(decision), {result: 'Confirmed', rationale: 'I confirm.', decidedBy: 'User via Codex'});
  assert.equal(reviewDecision({changes: [['status', 'Running', 'Completed']]}), null);
});

test('a terminal run does not present unchanged start notes as a fresh result', () => {
  const history = [{action: 'Created', changes: [['status', null, 'Running'], ['note', null, 'Inspect the UI.']]}];
  assert.deepEqual(runReportNotes({status: 'Completed', note: 'Inspect the UI.'}, history), {
    latest: 'Inspect the UI.', initial: '', unchanged: true,
  });
  assert.deepEqual(runReportNotes({status: 'Completed', note: 'Build passed.'}, history), {
    latest: 'Build passed.', initial: 'Inspect the UI.', unchanged: false,
  });
});

test('only the literal saved initial note is removed from the start of an appended report', () => {
  const initial = 'Inspect the UI.\nPreserve the previous design.\n';
  const history = [{action: 'Created', changes: [['status', null, 'Running'], ['note', null, initial]]}];
  assert.deepEqual(runReportNotes({status: 'Completed', note: initial + '\nBuild passed.\nUI checks passed.'}, history), {
    latest: 'Build passed.\nUI checks passed.', initial, unchanged: false,
  });
  const rewritten = 'Inspect the UI.\nThe previous design was reviewed.\nBuild passed.';
  assert.deepEqual(runReportNotes({status: 'Completed', note: rewritten}, history), {
    latest: rewritten, initial, unchanged: false,
  });
});

test('reports created after completion and reports with no audit history keep their recorded notes', () => {
  const completed = {status: 'Completed', note: 'Build passed.'};
  const history = [{action: 'Created', changes: [['status', null, 'Completed'], ['note', null, 'Build passed.']]}];
  const expected = {latest: 'Build passed.', initial: '', unchanged: false};
  assert.deepEqual(runReportNotes(completed, history), expected);
  assert.deepEqual(runReportNotes(completed, []), expected);
});
