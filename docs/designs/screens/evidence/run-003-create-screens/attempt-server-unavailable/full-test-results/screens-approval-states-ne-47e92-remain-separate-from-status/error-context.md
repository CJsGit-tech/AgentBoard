# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: screens.spec.ts >> approval states never apply changes and badges remain separate from status
- Location: tests/screens.spec.ts:415:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/tickets/8f24c9e7
Call log:
  - navigating to "http://127.0.0.1:4203/#/tickets/8f24c9e7", waiting until "load"

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
  1   | import { test, expect, Page } from "@playwright/test";
  2   | const nav = (page: Page, name: string) =>
  3   |   page
  4   |     .getByRole("navigation", { name: "Project navigation" })
  5   |     .getByRole("link", { name, exact: true });
  6   | const modal = (page: Page) => page.getByRole("dialog");
  7   | async function ticket(page: Page) {
> 8   |   await page.goto("/#/tickets/8f24c9e7");
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/tickets/8f24c9e7
  9   |   await expect(page.getByLabel("Ticket title", { exact: true })).toHaveValue(
  10  |     "Build MCP ticket tools",
  11  |   );
  12  | }
  13  | 
  14  | test("all screens render without runtime errors and all main navigation works", async ({
  15  |   page,
  16  | }) => {
  17  |   const errors: string[] = [];
  18  |   page.on("pageerror", (e) => errors.push(e.message));
  19  |   for (const [route, heading] of [
  20  |     ["/projects", "Projects"],
  21  |     ["/overview", "AgentBoard"],
  22  |     ["/roles", "Roles"],
  23  |     ["/tickets", "Tickets"],
  24  |     ["/documents", "Documents"],
  25  |     ["/documents/doc-mcp", "MCP ticket tool contract"],
  26  |     ["/documents/doc-mcp/history", "Revision history"],
  27  |     ["/activity", "Activity"],
  28  |   ]) {
  29  |     await page.goto("/#" + route);
  30  |     await expect(
  31  |       page.getByRole("heading", { name: heading, exact: true }).first(),
  32  |     ).toBeVisible();
  33  |   }
  34  |   await nav(page, "Overview").click();
  35  |   await expect(
  36  |     page.getByRole("heading", { name: "Project totals", exact: true }),
  37  |   ).toBeVisible();
  38  |   await nav(page, "Tickets").click();
  39  |   await expect(
  40  |     page.getByRole("table", { name: "Project tickets" }),
  41  |   ).toBeVisible();
  42  |   await nav(page, "Roles").click();
  43  |   await expect(
  44  |     page.getByText("Roles are definitions, not running agents.", {
  45  |       exact: false,
  46  |     }),
  47  |   ).toBeVisible();
  48  |   await nav(page, "Documents").click();
  49  |   await expect(
  50  |     page.getByRole("table", { name: "Project documents" }),
  51  |   ).toBeVisible();
  52  |   expect(errors).toEqual([]);
  53  | });
  54  | 
  55  | test("project validation, failure retention, create and switch keep project context isolated", async ({
  56  |   page,
  57  | }) => {
  58  |   await page.goto("/#/projects");
  59  |   await page.getByRole("button", { name: "New project", exact: true }).click();
  60  |   await expect(
  61  |     modal(page).getByRole("textbox", { name: "Project name", exact: true }),
  62  |   ).toHaveAccessibleName("Project name");
  63  |   await modal(page)
  64  |     .getByRole("button", { name: "Create project", exact: true })
  65  |     .click();
  66  |   await expect(modal(page).getByRole("alert")).toContainText(
  67  |     "Enter a project name",
  68  |   );
  69  |   await modal(page)
  70  |     .getByRole("textbox", { name: "Project name", exact: true })
  71  |     .fill("Research lab");
  72  |   await modal(page)
  73  |     .getByLabel("Purpose", { exact: true })
  74  |     .fill("Explore focused ideas");
  75  |   await page.getByLabel("Fail next save").check();
  76  |   await modal(page)
  77  |     .getByRole("button", { name: "Create project", exact: true })
  78  |     .click();
  79  |   await expect(page.getByRole("status")).toContainText("Save failed");
  80  |   await expect(modal(page).getByLabel("Purpose", { exact: true })).toHaveValue(
  81  |     "Explore focused ideas",
  82  |   );
  83  |   await modal(page)
  84  |     .getByRole("button", { name: "Create project", exact: true })
  85  |     .click();
  86  |   await expect(modal(page)).toHaveCount(0);
  87  |   await expect(
  88  |     page.getByRole("heading", { name: "Research lab", exact: true }),
  89  |   ).toBeVisible();
  90  |   await nav(page, "Tickets").click();
  91  |   await expect(
  92  |     page.getByRole("heading", { name: "No matching tickets", exact: true }),
  93  |   ).toBeVisible();
  94  |   await page
  95  |     .getByLabel("Select project", { exact: true })
  96  |     .selectOption("agentboard");
  97  |   await expect(
  98  |     page.getByRole("heading", { name: "AgentBoard", exact: true }),
  99  |   ).toBeVisible();
  100 |   await nav(page, "Tickets").click();
  101 |   await expect(
  102 |     page.getByRole("table", { name: "Project tickets" }),
  103 |   ).toBeVisible();
  104 |   await expect(
  105 |     page.getByRole("link", { name: "Build MCP ticket tools", exact: true }),
  106 |   ).toBeVisible();
  107 |   await page
  108 |     .getByLabel("Select project", { exact: true })
```