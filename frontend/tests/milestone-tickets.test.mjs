import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const source = await readFile(new URL("../src/features/tickets/milestone.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText;
const { milestoneFromTicketRoute, withMilestoneTicketFilter, ticketsForMilestone } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);

test("milestone tickets and counts share the same project-bound relationship", () => {
  const milestone = { id: "M-one", project: "P-one" };
  const matching = { id: "AB-one", project: "P-one", milestone: "M-one" };
  const differentMilestone = { id: "AB-two", project: "P-one", milestone: "M-two" };
  const differentProject = { id: "AB-three", project: "P-two", milestone: "M-one" };
  assert.deepEqual(ticketsForMilestone([matching, differentMilestone, differentProject], milestone), [matching]);
});

test("milestone drilldown query survives direct navigation and clears without changing the ticket view", () => {
  const route = "#project/P-one/tickets/overdue?existing=yes";
  const filtered = withMilestoneTicketFilter(route, "M-one");
  assert.equal(filtered, `${route}&milestone=M-one`);
  assert.equal(milestoneFromTicketRoute(filtered), "M-one");
  assert.equal(withMilestoneTicketFilter(filtered, ""), route);
  assert.equal(milestoneFromTicketRoute("#project/P-one/tickets/AB-one?milestone=M-one"), "");
  assert.equal(milestoneFromTicketRoute("#project/P-one/milestones?milestone=M-one"), "");
});
