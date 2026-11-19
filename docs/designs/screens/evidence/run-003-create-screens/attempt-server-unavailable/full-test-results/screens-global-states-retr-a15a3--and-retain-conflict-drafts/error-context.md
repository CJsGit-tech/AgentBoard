# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: screens.spec.ts >> global states retry, recover connection and retain conflict drafts
- Location: tests/screens.spec.ts:488:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/overview
Call log:
  - navigating to "http://127.0.0.1:4203/#/overview", waiting until "load"

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e6]:
    - heading "This site can’t be reached" [level=1] [ref=e7]
    - paragraph [ref=e8]:
      - strong [ref=e9]: 127.0.0.1
      - text: refused to connect.
    - generic [ref=e10]:
      - paragraph [ref=e11]: "Try:"
      - list [ref=e12]:
        - listitem [ref=e13]: Checking the connection
        - listitem [ref=e14]:
          - link "Checking the proxy and the firewall" [ref=e15] [cursor=pointer]:
            - /url: "#buttons"
    - generic [ref=e16]: ERR_CONNECTION_REFUSED
  - generic [ref=e17]:
    - button "Reload" [ref=e19] [cursor=pointer]
    - button "Details" [ref=e20] [cursor=pointer]
```

# Test source

```ts
  391 |   await page
  392 |     .getByRole("button", { name: "Confirm restore", exact: true })
  393 |     .click();
  394 |   await expect(page.locator(".revision-list li")).toHaveCount(4);
  395 |   await expect(page.locator(".revision-list")).toContainText("Version 5");
  396 |   await expect(page.locator(".revision-list")).not.toContainText("Version 1");
  397 |   await page
  398 |     .getByRole("button", { name: "Inspect expired version", exact: true })
  399 |     .click();
  400 |   await expect(
  401 |     page.getByRole("heading", {
  402 |       name: "This revision is no longer available",
  403 |       exact: true,
  404 |     }),
  405 |   ).toBeVisible();
  406 |   await page
  407 |     .getByRole("button", { name: "Return to retained versions", exact: true })
  408 |     .click();
  409 |   await page
  410 |     .getByRole("button", { name: "← Read document", exact: true })
  411 |     .click();
  412 |   await expect(page.locator(".docmeta")).toContainText("Version 5");
  413 | });
  414 | 
  415 | test("approval states never apply changes and badges remain separate from status", async ({
  416 |   page,
  417 | }) => {
  418 |   await ticket(page);
  419 |   await expect(page.locator(".badges .status")).toContainText("In progress");
  420 |   await expect(page.locator(".badges .approval")).toContainText(
  421 |     "Needs approval · 2",
  422 |   );
  423 |   await expect(page.locator(".request-card")).toHaveCount(2);
  424 |   for (const state of ["Unsupported", "Stale", "Expired", "Rejected"]) {
  425 |     await page.getByLabel("Approval request state").selectOption(state);
  426 |     await expect(page.locator(".request-card").first()).toContainText(state);
  427 |     await expect(page.getByLabel("Ticket status", { exact: true })).toHaveValue(
  428 |       "In progress",
  429 |     );
  430 |   }
  431 |   await expect(page.getByRole("button", { name: /^Approve$/ })).toHaveCount(0);
  432 |   await expect(page.locator(".ticket-inspector")).toContainText(
  433 |     "No business change was applied",
  434 |   );
  435 | });
  436 | 
  437 | test("activity filters, duplicate keys, disconnect/reconnect and retention preserve records", async ({
  438 |   page,
  439 | }) => {
  440 |   await page.goto("/#/activity");
  441 |   await expect(page.locator(".activity-feed")).not.toContainText(
  442 |     "Expired example event",
  443 |   );
  444 |   await page
  445 |     .getByLabel("Filter activity by provenance")
  446 |     .selectOption("Agent-reported");
  447 |   await expect(page.locator(".activity-feed li")).toHaveCount(1);
  448 |   await page.getByLabel("Filter activity by label").selectOption("frontend");
  449 |   await expect(page.locator(".activity-feed")).toContainText("Claude");
  450 |   await page.getByLabel("Filter activity by label").selectOption("");
  451 |   await page.getByLabel("Filter activity by provenance").selectOption("");
  452 |   await page.getByRole("button", { name: "Show activity from Claude", exact: true }).first().click();
  453 |   await expect(page.getByLabel("Filter activity by agent", { exact: true })).toHaveValue("Claude");
  454 |   await page.getByRole("button", { name: "Show activity labeled frontend", exact: true }).first().click();
  455 |   await expect(page.getByLabel("Filter activity by label", { exact: true })).toHaveValue("frontend");
  456 |   await page.getByLabel("Filter activity by agent", { exact: true }).selectOption("");
  457 |   await page.getByLabel("Filter activity by label", { exact: true }).selectOption("");
  458 |   const before = await page.locator(".activity-feed li").count();
  459 |   await page
  460 |     .getByRole("button", { name: "Simulate incoming event", exact: true })
  461 |     .click();
  462 |   await expect(page.locator(".activity-feed li")).toHaveCount(before + 1);
  463 |   await page
  464 |     .getByRole("button", { name: "Replay last event", exact: true })
  465 |     .click();
  466 |   await expect(page.locator(".activity-feed li")).toHaveCount(before + 1);
  467 |   await page
  468 |     .getByRole("button", { name: "Simulate disconnect", exact: true })
  469 |     .click();
  470 |   await page
  471 |     .getByRole("button", { name: "Simulate incoming event", exact: true })
  472 |     .click();
  473 |   await expect(
  474 |     page.getByRole("button", { name: "1 new event · Show", exact: true }),
  475 |   ).toBeVisible();
  476 |   await page.getByRole("button", { name: "Reconnect", exact: true }).click();
  477 |   await expect(page.locator(".live-state")).toContainText("Live preview");
  478 |   await expect(page.locator(".notice")).toContainText("unavailable interval");
  479 |   await page
  480 |     .getByRole("button", { name: "Run retention cleanup", exact: true })
  481 |     .click();
  482 |   await nav(page, "Documents").click();
  483 |   await expect(page.locator("tbody tr")).toHaveCount(2);
  484 |   await nav(page, "Tickets").click();
  485 |   await expect(page.locator("tbody tr")).toHaveCount(6);
  486 | });
  487 | 
  488 | test("global states retry, recover connection and retain conflict drafts", async ({
  489 |   page,
  490 | }) => {
> 491 |   await page.goto("/#/overview");
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/overview
  492 |   await page.getByLabel("Preview state", { exact: true }).selectOption("Error");
  493 |   await expect(
  494 |     page.getByRole("heading", {
  495 |       name: "Unable to load this view",
  496 |       exact: true,
  497 |     }),
  498 |   ).toBeVisible();
  499 |   await page.getByRole("button", { name: "Retry", exact: true }).click();
  500 |   await expect(
  501 |     page.getByRole("heading", { name: "Project totals", exact: true }),
  502 |   ).toBeVisible();
  503 |   await page
  504 |     .getByLabel("Preview state", { exact: true })
  505 |     .selectOption("Loading");
  506 |   await expect(
  507 |     page.getByRole("heading", { name: "Loading workspace…", exact: true }),
  508 |   ).toBeVisible();
  509 |   await page.getByLabel("Preview state", { exact: true }).selectOption("Ready");
  510 |   await nav(page, "Activity").click();
  511 |   await page
  512 |     .getByLabel("Preview state", { exact: true })
  513 |     .selectOption("Disconnected");
  514 |   await page.getByRole("button", { name: "Reconnect", exact: true }).click();
  515 |   await expect(page.getByLabel("Preview state", { exact: true })).toHaveValue(
  516 |     "Ready",
  517 |   );
  518 |   await page.goto("/#/documents/doc-mcp");
  519 |   await page
  520 |     .getByRole("button", { name: "Edit document", exact: true })
  521 |     .click();
  522 |   await page
  523 |     .getByLabel("Document content", { exact: true })
  524 |     .fill("My unsaved draft");
  525 |   await page
  526 |     .getByLabel("Preview state", { exact: true })
  527 |     .selectOption("Conflict");
  528 |   await page
  529 |     .getByRole("button", { name: "Save document", exact: true })
  530 |     .click();
  531 |   await expect(
  532 |     page.getByLabel("Document content", { exact: true }),
  533 |   ).toHaveValue("My unsaved draft");
  534 |   await expect(page.locator(".conflict-panel")).toContainText(
  535 |     "Current saved content",
  536 |   );
  537 | });
  538 | 
  539 | test("desktop responsive layouts and control focus stay contained", async ({
  540 |   page,
  541 | }) => {
  542 |   const errors: string[] = [];
  543 |   page.on("pageerror", (e) => errors.push(e.message));
  544 |   for (const width of [1600, 1280, 900]) {
  545 |     await page.setViewportSize({ width, height: 1000 });
  546 |     await page.goto("/#/tickets");
  547 |     await page.getByRole("button", { name: "▥ Board", exact: true }).focus();
  548 |     await page.keyboard.press("Tab");
  549 |     const style = await page
  550 |       .getByLabel("Filter tickets by status")
  551 |       .evaluate((e) => {
  552 |         const s = getComputedStyle(e);
  553 |         return {
  554 |           outline: s.outlineStyle,
  555 |           shadow: s.boxShadow,
  556 |           padding: parseInt(s.paddingRight),
  557 |           position: s.backgroundPosition,
  558 |           focused: document.activeElement === e,
  559 |         };
  560 |       });
  561 |     expect(style.focused).toBe(true);
  562 |     expect(style.outline).toBe("none");
  563 |     expect(style.shadow).toContain("inset");
  564 |     expect(style.padding).toBeGreaterThanOrEqual(32);
  565 |     expect(style.position).toContain("10px");
  566 |     expect(
  567 |       await page.evaluate(
  568 |         () => document.documentElement.scrollWidth <= innerWidth,
  569 |       ),
  570 |     ).toBe(true);
  571 |     await page.goto("/#/documents/doc-mcp/history");
  572 |     await expect(
  573 |       page.getByRole("heading", { name: "Revision history", exact: true }),
  574 |     ).toBeVisible();
  575 |     expect(
  576 |       await page.evaluate(
  577 |         () => document.documentElement.scrollWidth <= innerWidth,
  578 |       ),
  579 |     ).toBe(true);
  580 |   }
  581 |   expect(errors).toEqual([]);
  582 | });
  583 | 
  584 | test("native modal keeps page inert, restores invoker focus and has contrasting internal focus", async ({
  585 |   page,
  586 | }) => {
  587 |   await page.goto("/#/projects");
  588 |   await page.getByRole("button", { name: "New project", exact: true }).click();
  589 |   const save = modal(page).getByRole("button", {
  590 |     name: "Create project",
  591 |     exact: true,
```