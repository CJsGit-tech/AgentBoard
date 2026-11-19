# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: screens.spec.ts >> ticket create and board use shared records and explicit statuses
- Location: tests/screens.spec.ts:249:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/tickets
Call log:
  - navigating to "http://127.0.0.1:4203/#/tickets", waiting until "load"

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
  152 |   await expect(
  153 |     modal(page).getByRole("textbox", { name: "Role name", exact: true }),
  154 |   ).toHaveAccessibleName("Role name");
  155 |   await modal(page)
  156 |     .getByRole("button", { name: "Save role", exact: true })
  157 |     .click();
  158 |   await expect(modal(page).getByRole("alert")).toContainText("required");
  159 |   await modal(page)
  160 |     .getByRole("textbox", { name: "Role name", exact: true })
  161 |     .fill("QA");
  162 |   await modal(page)
  163 |     .getByLabel("Responsibilities", { exact: true })
  164 |     .fill("Independently verify product flows");
  165 |   await modal(page)
  166 |     .getByRole("button", { name: "Save role", exact: true })
  167 |     .click();
  168 |   await expect(
  169 |     page.getByRole("heading", { name: "QA", exact: true }),
  170 |   ).toBeVisible();
  171 |   await page
  172 |     .locator(".role-card")
  173 |     .filter({
  174 |       has: page.getByRole("heading", { name: "Backend", exact: true }),
  175 |     })
  176 |     .getByRole("button", { name: "Edit", exact: true })
  177 |     .click();
  178 |   await modal(page)
  179 |     .getByLabel("Responsibilities", { exact: true })
  180 |     .fill("Maintain typed tools and explicit approval boundaries");
  181 |   await modal(page)
  182 |     .getByRole("button", { name: "Save role", exact: true })
  183 |     .click();
  184 |   await nav(page, "Tickets").click();
  185 |   await page
  186 |     .getByRole("link", { name: "Build MCP ticket tools", exact: true })
  187 |     .click();
  188 |   await expect(page.getByLabel("Ticket owner", { exact: true })).toHaveValue(
  189 |     "backend",
  190 |   );
  191 |   await expect(
  192 |     page.getByLabel("Ticket owner", { exact: true }),
  193 |   ).not.toContainText("Researcher");
  194 |   await expect(page.getByLabel("Ticket owner", { exact: true })).toContainText(
  195 |     "QA",
  196 |   );
  197 | });
  198 | 
  199 | test("ticket validation, failed save, reassignment and status changes stay consistent", async ({
  200 |   page,
  201 | }) => {
  202 |   await ticket(page);
  203 |   await page
  204 |     .getByLabel("Ticket status", { exact: true })
  205 |     .selectOption("Blocked");
  206 |   await page.getByRole("button", { name: "Save ticket", exact: true }).click();
  207 |   await expect(page.getByRole("alert")).toContainText("Explain the blocker");
  208 |   await page
  209 |     .getByLabel("Blocker explanation", { exact: true })
  210 |     .fill("Waiting on contract review");
  211 |   await page.getByLabel("Fail next save").check();
  212 |   await page.getByRole("button", { name: "Save ticket", exact: true }).click();
  213 |   await expect(page.getByRole("status")).toContainText("Save failed");
  214 |   await expect(
  215 |     page
  216 |       .locator("tbody tr")
  217 |       .filter({ hasText: "Build MCP ticket tools" })
  218 |       .locator(".status"),
  219 |   ).toContainText("In progress");
  220 |   await page.getByText("Ticket activity", { exact: true }).click();
  221 |   await expect(
  222 |     page.locator(".ticket-inspector .activity-feed"),
  223 |   ).not.toContainText("Status: In progress → Blocked");
  224 |   await page.getByRole("button", { name: "Save ticket", exact: true }).click();
  225 |   await expect(
  226 |     page
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
> 252 |   await page.goto("/#/tickets");
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/tickets
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
  327 |   await page.goto("/#/documents");
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
```