# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: screens.spec.ts >> role create/edit keeps assignments and filters owners by project
- Location: tests/screens.spec.ts:146:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/roles
Call log:
  - navigating to "http://127.0.0.1:4203/#/roles", waiting until "load"

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
  109 |     .selectOption("fieldnotes");
  110 |   await expect(
  111 |     page.getByRole("heading", { name: "Fieldnotes", exact: true }),
  112 |   ).toBeVisible();
  113 |   await nav(page, "Documents").click();
  114 |   await expect(
  115 |     page.getByRole("heading", { name: "No documents found", exact: true }),
  116 |   ).toBeVisible();
  117 | });
  118 | 
  119 | test("project edit preserves associations and has no discard dialog after save", async ({
  120 |   page,
  121 | }) => {
  122 |   await page.goto("/#/projects");
  123 |   await expect(page.locator(".project-card").filter({ hasText: "AgentBoard" }).getByRole("button", { name: "Edit", exact: true })).toHaveAccessibleDescription("AgentBoard");
  124 |   await page
  125 |     .locator(".project-card")
  126 |     .filter({ hasText: "AgentBoard" })
  127 |     .getByRole("button", { name: "Edit", exact: true })
  128 |     .click();
  129 |   await modal(page)
  130 |     .getByRole("textbox", { name: "Project name", exact: true })
  131 |     .fill("AgentBoard revised");
  132 |   let dialogs = 0;
  133 |   page.on("dialog", async (dialog) => {
  134 |     dialogs++;
  135 |     await dialog.dismiss();
  136 |   });
  137 |   await modal(page)
  138 |     .getByRole("button", { name: "Save project", exact: true })
  139 |     .click();
  140 |   await expect(modal(page)).toHaveCount(0);
  141 |   expect(dialogs).toBe(0);
  142 |   await nav(page, "Tickets").click();
  143 |   await expect(page.locator("tbody tr")).toHaveCount(6);
  144 | });
  145 | 
  146 | test("role create/edit keeps assignments and filters owners by project", async ({
  147 |   page,
  148 | }) => {
> 149 |   await page.goto("/#/roles");
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:4203/#/roles
  150 |   await expect(page.locator(".role-card").filter({ has: page.getByRole("heading", { name: "Backend", exact: true }) }).getByRole("button", { name: "Edit", exact: true })).toHaveAccessibleDescription("Backend");
  151 |   await page.getByRole("button", { name: "New role", exact: true }).click();
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
```