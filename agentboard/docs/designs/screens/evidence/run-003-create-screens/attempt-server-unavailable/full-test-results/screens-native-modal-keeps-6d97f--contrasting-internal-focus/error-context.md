# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: screens.spec.ts >> native modal keeps page inert, restores invoker focus and has contrasting internal focus
- Location: tests/screens.spec.ts:584:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/projects
Call log:
  - navigating to "http://127.0.0.1:4203/#/projects", waiting until "load"

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
  487 | 
  488 | test("global states retry, recover connection and retain conflict drafts", async ({
  489 |   page,
  490 | }) => {
  491 |   await page.goto("/#/overview");
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
> 587 |   await page.goto("/#/projects");
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/projects
  588 |   await page.getByRole("button", { name: "New project", exact: true }).click();
  589 |   const save = modal(page).getByRole("button", {
  590 |     name: "Create project",
  591 |     exact: true,
  592 |   });
  593 |   const close = modal(page).getByRole("button", {
  594 |     name: "Close dialog",
  595 |     exact: true,
  596 |   });
  597 |   await save.focus();
  598 |   await page.keyboard.press("Tab");
  599 |   expect(
  600 |     await page.evaluate(
  601 |       () =>
  602 |         document.activeElement === document.body ||
  603 |         !!document.querySelector("dialog")?.contains(document.activeElement),
  604 |     ),
  605 |   ).toBe(true);
  606 |   await page.keyboard.press("Shift+Tab");
  607 |   expect(
  608 |     await page.evaluate(
  609 |       () =>
  610 |         document.activeElement === document.body ||
  611 |         !!document.querySelector("dialog")?.contains(document.activeElement),
  612 |     ),
  613 |   ).toBe(true);
  614 |   await save.focus();
  615 |   const focus = await save.evaluate((e) => ({
  616 |     shadow: getComputedStyle(e).boxShadow,
  617 |     background: getComputedStyle(e).backgroundColor,
  618 |   }));
  619 |   expect(focus.shadow).toContain("inset");
  620 |   expect(focus.shadow).toContain("255, 255, 255");
  621 |   expect(focus.background).not.toBe("rgb(255, 255, 255)");
  622 |   await close.click();
  623 |   await expect(
  624 |     page.getByRole("button", { name: "New project", exact: true }),
  625 |   ).toBeFocused();
  626 | });
  627 | 
```