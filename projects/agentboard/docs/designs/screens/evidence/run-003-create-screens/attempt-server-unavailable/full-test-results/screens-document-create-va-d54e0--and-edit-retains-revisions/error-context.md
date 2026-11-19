# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: screens.spec.ts >> document create validates, preserves failed input, and edit retains revisions
- Location: tests/screens.spec.ts:324:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/documents
Call log:
  - navigating to "http://127.0.0.1:4203/#/documents", waiting until "load"

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
  227 |       .locator("tbody tr")
  228 |       .filter({ hasText: "Build MCP ticket tools" })
  229 |       .locator(".status"),
  230 |   ).toContainText("Blocked");
  231 |   await expect(page.locator(".ticket-inspector .activity-feed")).toContainText(
  232 |     "Status: In progress → Blocked",
  233 |   );
  234 |   await page.getByLabel("Ticket owner", { exact: true }).selectOption("me");
  235 |   await page.getByLabel("Ticket status", { exact: true }).selectOption("Done");
  236 |   await page.getByRole("button", { name: "Save ticket", exact: true }).click();
  237 |   await nav(page, "Overview").click();
  238 |   await expect(
  239 |     page.locator(".status-counts button").filter({ hasText: "Done" }),
  240 |   ).toContainText("2");
  241 |   await page
  242 |     .locator(".status-counts button")
  243 |     .filter({ hasText: "Done" })
  244 |     .click();
  245 |   await expect(page.getByLabel("Filter tickets by status")).toHaveValue("Done");
  246 |   await expect(page.locator("tbody tr")).toHaveCount(2);
  247 | });
  248 | 
  249 | test("ticket create and board use shared records and explicit statuses", async ({
  250 |   page,
  251 | }) => {
  252 |   await page.goto("/#/tickets");
  253 |   await page.getByRole("button", { name: "New ticket", exact: true }).click();
  254 |   await page
  255 |     .getByRole("button", { name: "Create ticket", exact: true })
  256 |     .click();
  257 |   await expect(page.getByRole("alert")).toContainText("title");
  258 |   await page
  259 |     .getByLabel("Ticket title", { exact: true })
  260 |     .fill("Review screen coverage");
  261 |   await page.getByLabel("Ticket owner", { exact: true }).selectOption("me");
  262 |   await page
  263 |     .getByLabel("Ticket priority", { exact: true })
  264 |     .selectOption("High");
  265 |   await page
  266 |     .getByRole("button", { name: "Create ticket", exact: true })
  267 |     .click();
  268 |   await expect(
  269 |     page.getByRole("link", { name: "Review screen coverage", exact: true }),
  270 |   ).toBeVisible();
  271 |   await page.getByRole("button", { name: "▥ Board", exact: true }).click();
  272 |   await expect(page.locator(".board-lane")).toHaveCount(4);
  273 |   await expect(
  274 |     page.locator(".board-lane").filter({ hasText: "Planned" }),
  275 |   ).toContainText("Review screen coverage");
  276 |   await page.getByRole("button", { name: "▤ Table", exact: true }).click();
  277 |   await page.getByLabel("Order tickets").selectOption("priority");
  278 |   await expect(page.locator("tbody tr").first()).toContainText("High");
  279 | });
  280 | 
  281 | test("document associations deduplicate, unlink without deleting and return to correct ticket", async ({
  282 |   page,
  283 | }) => {
  284 |   await ticket(page);
  285 |   await page
  286 |     .getByLabel("Link document", { exact: true })
  287 |     .selectOption("doc-mcp");
  288 |   await page
  289 |     .getByLabel("Document relationship", { exact: true })
  290 |     .selectOption("Context");
  291 |   await page.getByRole("button", { name: "Link", exact: true }).click();
  292 |   await expect(page.locator(".document-link")).toHaveCount(1);
  293 |   await page
  294 |     .getByLabel("Document relationship", { exact: true })
  295 |     .selectOption("Output");
  296 |   await page.getByRole("button", { name: "Link", exact: true }).click();
  297 |   await expect(page.locator(".document-link")).toHaveCount(2);
  298 |   await page.locator(".document-link").first().getByRole("link").click();
  299 |   await expect(
  300 |     page.getByRole("heading", {
  301 |       name: "MCP ticket tool contract",
  302 |       exact: true,
  303 |     }),
  304 |   ).toBeVisible();
  305 |   await page
  306 |     .getByRole("button", { name: "← Back to ticket", exact: true })
  307 |     .click();
  308 |   await expect(page.getByLabel("Ticket title", { exact: true })).toHaveValue(
  309 |     "Build MCP ticket tools",
  310 |   );
  311 |   await page
  312 |     .getByRole("button", {
  313 |       name: "Unlink MCP ticket tool contract Output",
  314 |       exact: true,
  315 |     })
  316 |     .click();
  317 |   await expect(page.locator(".document-link")).toHaveCount(1);
  318 |   await nav(page, "Documents").click();
  319 |   await expect(
  320 |     page.getByRole("link", { name: "MCP ticket tool contract", exact: true }),
  321 |   ).toBeVisible();
  322 | });
  323 | 
  324 | test("document create validates, preserves failed input, and edit retains revisions", async ({
  325 |   page,
  326 | }) => {
> 327 |   await page.goto("/#/documents");
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/documents
  328 |   await page.getByRole("button", { name: "New document", exact: true }).click();
  329 |   await modal(page)
  330 |     .getByRole("button", { name: "Save document", exact: true })
  331 |     .click();
  332 |   await expect(modal(page).getByRole("alert")).toContainText("required");
  333 |   await modal(page)
  334 |     .getByLabel("Document title", { exact: true })
  335 |     .fill("QA notes");
  336 |   await modal(page)
  337 |     .getByLabel("Document content", { exact: true })
  338 |     .fill("Checks\nReview every connected screen.");
  339 |   await page.getByLabel("Fail next save").check();
  340 |   await modal(page)
  341 |     .getByRole("button", { name: "Save document", exact: true })
  342 |     .click();
  343 |   await expect(
  344 |     modal(page).getByLabel("Document content", { exact: true }),
  345 |   ).toHaveValue("Checks\nReview every connected screen.");
  346 |   await modal(page)
  347 |     .getByRole("button", { name: "Save document", exact: true })
  348 |     .click();
  349 |   await expect(
  350 |     page.getByRole("heading", { name: "QA notes", exact: true }),
  351 |   ).toBeVisible();
  352 |   await page
  353 |     .getByRole("button", { name: "Edit document", exact: true })
  354 |     .click();
  355 |   await page
  356 |     .getByLabel("Document content", { exact: true })
  357 |     .fill("Checks\nAll screens were reviewed.");
  358 |   await page
  359 |     .getByRole("button", { name: "Save document", exact: true })
  360 |     .click();
  361 |   await page
  362 |     .getByRole("button", { name: "Revision history", exact: true })
  363 |     .click();
  364 |   await expect(page.locator(".revision-list li")).toHaveCount(2);
  365 |   await expect(page.getByLabel("Compare revision")).toContainText("Version 2");
  366 | });
  367 | 
  368 | test("arbitrary revision comparison, failed restore, successful restore and retention cap", async ({
  369 |   page,
  370 | }) => {
  371 |   await page.goto("/#/documents/doc-mcp/history");
  372 |   await expect(page.locator(".revision-list li")).toHaveCount(4);
  373 |   await page
  374 |     .getByLabel("Selected revision", { exact: true })
  375 |     .selectOption("rev-2");
  376 |   await page
  377 |     .getByLabel("Compare revision", { exact: true })
  378 |     .selectOption("rev-3");
  379 |   await expect(
  380 |     page.getByRole("heading", { name: "Version 2 → Version 3", exact: true }),
  381 |   ).toBeVisible();
  382 |   await page
  383 |     .getByRole("button", { name: "Restore version 2", exact: true })
  384 |     .click();
  385 |   await page.getByLabel("Fail next save").check();
  386 |   await page
  387 |     .getByRole("button", { name: "Confirm restore", exact: true })
  388 |     .click();
  389 |   await expect(page.locator(".revision-list li")).toHaveCount(4);
  390 |   await expect(page.locator(".revision-list")).not.toContainText("Version 5");
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
```