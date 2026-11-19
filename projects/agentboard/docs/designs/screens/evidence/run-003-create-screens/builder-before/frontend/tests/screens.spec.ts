import { test, expect, Page } from "@playwright/test";
const nav = (page: Page, name: string) =>
  page
    .getByRole("navigation", { name: "Project navigation" })
    .getByRole("link", { name, exact: true });
const modal = (page: Page) => page.getByRole("dialog");
async function ticket(page: Page) {
  await page.goto("/#/tickets/8f24c9e7");
  await expect(page.getByLabel("Ticket title", { exact: true })).toHaveValue(
    "Build MCP ticket tools",
  );
}

test("all screens render without runtime errors and all main navigation works", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const [route, heading] of [
    ["/projects", "Projects"],
    ["/overview", "AgentBoard"],
    ["/roles", "Roles"],
    ["/tickets", "Tickets"],
    ["/documents", "Documents"],
    ["/documents/doc-mcp", "MCP ticket tool contract"],
    ["/documents/doc-mcp/history", "Revision history"],
    ["/activity", "Activity"],
  ]) {
    await page.goto("/#" + route);
    await expect(
      page.getByRole("heading", { name: heading, exact: true }).first(),
    ).toBeVisible();
  }
  await nav(page, "Overview").click();
  await expect(
    page.getByRole("heading", { name: "Project totals", exact: true }),
  ).toBeVisible();
  await nav(page, "Tickets").click();
  await expect(
    page.getByRole("table", { name: "Project tickets" }),
  ).toBeVisible();
  await nav(page, "Roles").click();
  await expect(
    page.getByText("Roles are definitions, not running agents.", {
      exact: false,
    }),
  ).toBeVisible();
  await nav(page, "Documents").click();
  await expect(
    page.getByRole("table", { name: "Project documents" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("project validation, failure retention, create and switch keep project context isolated", async ({
  page,
}) => {
  await page.goto("/#/projects");
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await expect(
    modal(page).getByRole("textbox", { name: "Project name", exact: true }),
  ).toHaveAccessibleName("Project name");
  await modal(page)
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(modal(page).getByRole("alert")).toContainText(
    "Enter a project name",
  );
  await modal(page)
    .getByRole("textbox", { name: "Project name", exact: true })
    .fill("Research lab");
  await modal(page)
    .getByLabel("Purpose", { exact: true })
    .fill("Explore focused ideas");
  await page.getByLabel("Fail next save").check();
  await modal(page)
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Save failed");
  await expect(modal(page).getByLabel("Purpose", { exact: true })).toHaveValue(
    "Explore focused ideas",
  );
  await modal(page)
    .getByRole("button", { name: "Create project", exact: true })
    .click();
  await expect(modal(page)).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Research lab", exact: true }),
  ).toBeVisible();
  await nav(page, "Tickets").click();
  await expect(
    page.getByRole("heading", { name: "No matching tickets", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Select project", { exact: true })
    .selectOption("agentboard");
  await expect(
    page.getByRole("heading", { name: "AgentBoard", exact: true }),
  ).toBeVisible();
  await nav(page, "Tickets").click();
  await expect(
    page.getByRole("table", { name: "Project tickets" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Build MCP ticket tools", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Select project", { exact: true })
    .selectOption("fieldnotes");
  await expect(
    page.getByRole("heading", { name: "Fieldnotes", exact: true }),
  ).toBeVisible();
  await nav(page, "Documents").click();
  await expect(
    page.getByRole("heading", { name: "No documents found", exact: true }),
  ).toBeVisible();
});

test("project edit preserves associations and has no discard dialog after save", async ({
  page,
}) => {
  await page.goto("/#/projects");
  await page
    .locator(".project-card")
    .filter({ hasText: "AgentBoard" })
    .getByRole("button", { name: "Edit", exact: true })
    .click();
  await modal(page)
    .getByRole("textbox", { name: "Project name", exact: true })
    .fill("AgentBoard revised");
  let dialogs = 0;
  page.on("dialog", async (dialog) => {
    dialogs++;
    await dialog.dismiss();
  });
  await modal(page)
    .getByRole("button", { name: "Save project", exact: true })
    .click();
  await expect(modal(page)).toHaveCount(0);
  expect(dialogs).toBe(0);
  await nav(page, "Tickets").click();
  await expect(page.locator("tbody tr")).toHaveCount(6);
});

test("role create/edit keeps assignments and filters owners by project", async ({
  page,
}) => {
  await page.goto("/#/roles");
  await page.getByRole("button", { name: "New role", exact: true }).click();
  await expect(
    modal(page).getByRole("textbox", { name: "Role name", exact: true }),
  ).toHaveAccessibleName("Role name");
  await modal(page)
    .getByRole("button", { name: "Save role", exact: true })
    .click();
  await expect(modal(page).getByRole("alert")).toContainText("required");
  await modal(page)
    .getByRole("textbox", { name: "Role name", exact: true })
    .fill("QA");
  await modal(page)
    .getByLabel("Responsibilities", { exact: true })
    .fill("Independently verify product flows");
  await modal(page)
    .getByRole("button", { name: "Save role", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "QA", exact: true }),
  ).toBeVisible();
  await page
    .locator(".role-card")
    .filter({
      has: page.getByRole("heading", { name: "Backend", exact: true }),
    })
    .getByRole("button", { name: "Edit", exact: true })
    .click();
  await modal(page)
    .getByLabel("Responsibilities", { exact: true })
    .fill("Maintain typed tools and explicit approval boundaries");
  await modal(page)
    .getByRole("button", { name: "Save role", exact: true })
    .click();
  await nav(page, "Tickets").click();
  await page
    .getByRole("link", { name: "Build MCP ticket tools", exact: true })
    .click();
  await expect(page.getByLabel("Ticket owner", { exact: true })).toHaveValue(
    "backend",
  );
  await expect(
    page.getByLabel("Ticket owner", { exact: true }),
  ).not.toContainText("Researcher");
  await expect(page.getByLabel("Ticket owner", { exact: true })).toContainText(
    "QA",
  );
});

test("ticket validation, failed save, reassignment and status changes stay consistent", async ({
  page,
}) => {
  await ticket(page);
  await page
    .getByLabel("Ticket status", { exact: true })
    .selectOption("Blocked");
  await page.getByRole("button", { name: "Save ticket", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Explain the blocker");
  await page
    .getByLabel("Blocker explanation", { exact: true })
    .fill("Waiting on contract review");
  await page.getByLabel("Fail next save").check();
  await page.getByRole("button", { name: "Save ticket", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Save failed");
  await expect(
    page
      .locator("tbody tr")
      .filter({ hasText: "Build MCP ticket tools" })
      .locator(".status"),
  ).toContainText("In progress");
  await page.getByText("Ticket activity", { exact: true }).click();
  await expect(
    page.locator(".ticket-inspector .activity-feed"),
  ).not.toContainText("Status: In progress → Blocked");
  await page.getByRole("button", { name: "Save ticket", exact: true }).click();
  await expect(
    page
      .locator("tbody tr")
      .filter({ hasText: "Build MCP ticket tools" })
      .locator(".status"),
  ).toContainText("Blocked");
  await expect(page.locator(".ticket-inspector .activity-feed")).toContainText(
    "Status: In progress → Blocked",
  );
  await page.getByLabel("Ticket owner", { exact: true }).selectOption("me");
  await page.getByLabel("Ticket status", { exact: true }).selectOption("Done");
  await page.getByRole("button", { name: "Save ticket", exact: true }).click();
  await nav(page, "Overview").click();
  await expect(
    page.locator(".status-counts button").filter({ hasText: "Done" }),
  ).toContainText("2");
  await page
    .locator(".status-counts button")
    .filter({ hasText: "Done" })
    .click();
  await expect(page.getByLabel("Filter tickets by status")).toHaveValue("Done");
  await expect(page.locator("tbody tr")).toHaveCount(2);
});

test("ticket create and board use shared records and explicit statuses", async ({
  page,
}) => {
  await page.goto("/#/tickets");
  await page.getByRole("button", { name: "New ticket", exact: true }).click();
  await page
    .getByRole("button", { name: "Create ticket", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("title");
  await page
    .getByLabel("Ticket title", { exact: true })
    .fill("Review screen coverage");
  await page.getByLabel("Ticket owner", { exact: true }).selectOption("me");
  await page
    .getByLabel("Ticket priority", { exact: true })
    .selectOption("High");
  await page
    .getByRole("button", { name: "Create ticket", exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: "Review screen coverage", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "▥ Board", exact: true }).click();
  await expect(page.locator(".board-lane")).toHaveCount(4);
  await expect(
    page.locator(".board-lane").filter({ hasText: "Planned" }),
  ).toContainText("Review screen coverage");
  await page.getByRole("button", { name: "▤ Table", exact: true }).click();
  await page.getByLabel("Order tickets").selectOption("priority");
  await expect(page.locator("tbody tr").first()).toContainText("High");
});

test("document associations deduplicate, unlink without deleting and return to correct ticket", async ({
  page,
}) => {
  await ticket(page);
  await page
    .getByLabel("Link document", { exact: true })
    .selectOption("doc-mcp");
  await page
    .getByLabel("Document relationship", { exact: true })
    .selectOption("Context");
  await page.getByRole("button", { name: "Link", exact: true }).click();
  await expect(page.locator(".document-link")).toHaveCount(1);
  await page
    .getByLabel("Document relationship", { exact: true })
    .selectOption("Output");
  await page.getByRole("button", { name: "Link", exact: true }).click();
  await expect(page.locator(".document-link")).toHaveCount(2);
  await page.locator(".document-link").first().getByRole("link").click();
  await expect(
    page.getByRole("heading", {
      name: "MCP ticket tool contract",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "← Back to ticket", exact: true })
    .click();
  await expect(page.getByLabel("Ticket title", { exact: true })).toHaveValue(
    "Build MCP ticket tools",
  );
  await page
    .getByRole("button", {
      name: "Unlink MCP ticket tool contract Output",
      exact: true,
    })
    .click();
  await expect(page.locator(".document-link")).toHaveCount(1);
  await nav(page, "Documents").click();
  await expect(
    page.getByRole("link", { name: "MCP ticket tool contract", exact: true }),
  ).toBeVisible();
});

test("document create validates, preserves failed input, and edit retains revisions", async ({
  page,
}) => {
  await page.goto("/#/documents");
  await page.getByRole("button", { name: "New document", exact: true }).click();
  await modal(page)
    .getByRole("button", { name: "Save document", exact: true })
    .click();
  await expect(modal(page).getByRole("alert")).toContainText("required");
  await modal(page)
    .getByLabel("Document title", { exact: true })
    .fill("QA notes");
  await modal(page)
    .getByLabel("Document content", { exact: true })
    .fill("Checks\nReview every connected screen.");
  await page.getByLabel("Fail next save").check();
  await modal(page)
    .getByRole("button", { name: "Save document", exact: true })
    .click();
  await expect(
    modal(page).getByLabel("Document content", { exact: true }),
  ).toHaveValue("Checks\nReview every connected screen.");
  await modal(page)
    .getByRole("button", { name: "Save document", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "QA notes", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Edit document", exact: true })
    .click();
  await page
    .getByLabel("Document content", { exact: true })
    .fill("Checks\nAll screens were reviewed.");
  await page
    .getByRole("button", { name: "Save document", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Revision history", exact: true })
    .click();
  await expect(page.locator(".revision-list li")).toHaveCount(2);
  await expect(page.getByLabel("Compare revision")).toContainText("Version 2");
});

test("arbitrary revision comparison, failed restore, successful restore and retention cap", async ({
  page,
}) => {
  await page.goto("/#/documents/doc-mcp/history");
  await expect(page.locator(".revision-list li")).toHaveCount(4);
  await page
    .getByLabel("Selected revision", { exact: true })
    .selectOption("rev-2");
  await page
    .getByLabel("Compare revision", { exact: true })
    .selectOption("rev-3");
  await expect(
    page.getByRole("heading", { name: "Version 2 → Version 3", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Restore version 2", exact: true })
    .click();
  await page.getByLabel("Fail next save").check();
  await page
    .getByRole("button", { name: "Confirm restore", exact: true })
    .click();
  await expect(page.locator(".revision-list li")).toHaveCount(4);
  await expect(page.locator(".revision-list")).not.toContainText("Version 5");
  await page
    .getByRole("button", { name: "Confirm restore", exact: true })
    .click();
  await expect(page.locator(".revision-list li")).toHaveCount(4);
  await expect(page.locator(".revision-list")).toContainText("Version 5");
  await expect(page.locator(".revision-list")).not.toContainText("Version 1");
  await page
    .getByRole("button", { name: "Inspect expired version", exact: true })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "This revision is no longer available",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Return to retained versions", exact: true })
    .click();
  await page
    .getByRole("button", { name: "← Read document", exact: true })
    .click();
  await expect(page.locator(".docmeta")).toContainText("Version 5");
});

test("approval states never apply changes and badges remain separate from status", async ({
  page,
}) => {
  await ticket(page);
  await expect(page.locator(".badges .status")).toContainText("In progress");
  await expect(page.locator(".badges .approval")).toContainText(
    "Needs approval · 2",
  );
  await expect(page.locator(".request-card")).toHaveCount(2);
  for (const state of ["Unsupported", "Stale", "Expired", "Rejected"]) {
    await page.getByLabel("Approval request state").selectOption(state);
    await expect(page.locator(".request-card").first()).toContainText(state);
    await expect(page.getByLabel("Ticket status", { exact: true })).toHaveValue(
      "In progress",
    );
  }
  await expect(page.getByRole("button", { name: /^Approve$/ })).toHaveCount(0);
  await expect(page.locator(".ticket-inspector")).toContainText(
    "No business change was applied",
  );
});

test("activity filters, duplicate keys, disconnect/reconnect and retention preserve records", async ({
  page,
}) => {
  await page.goto("/#/activity");
  await expect(page.locator(".activity-feed")).not.toContainText(
    "Expired example event",
  );
  await page
    .getByLabel("Filter activity by provenance")
    .selectOption("Agent-reported");
  await expect(page.locator(".activity-feed li")).toHaveCount(1);
  await page.getByLabel("Filter activity by label").selectOption("frontend");
  await expect(page.locator(".activity-feed")).toContainText("Claude");
  await page.getByLabel("Filter activity by label").selectOption("");
  await page.getByLabel("Filter activity by provenance").selectOption("");
  const before = await page.locator(".activity-feed li").count();
  await page
    .getByRole("button", { name: "Simulate incoming event", exact: true })
    .click();
  await expect(page.locator(".activity-feed li")).toHaveCount(before + 1);
  await page
    .getByRole("button", { name: "Replay last event", exact: true })
    .click();
  await expect(page.locator(".activity-feed li")).toHaveCount(before + 1);
  await page
    .getByRole("button", { name: "Simulate disconnect", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Simulate incoming event", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "1 new event · Show", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Reconnect", exact: true }).click();
  await expect(page.locator(".live-state")).toContainText("Live preview");
  await expect(page.locator(".notice")).toContainText("unavailable interval");
  await page
    .getByRole("button", { name: "Run retention cleanup", exact: true })
    .click();
  await nav(page, "Documents").click();
  await expect(page.locator("tbody tr")).toHaveCount(2);
  await nav(page, "Tickets").click();
  await expect(page.locator("tbody tr")).toHaveCount(6);
});

test("global states retry, recover connection and retain conflict drafts", async ({
  page,
}) => {
  await page.goto("/#/overview");
  await page.getByLabel("Preview state", { exact: true }).selectOption("Error");
  await expect(
    page.getByRole("heading", {
      name: "Unable to load this view",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Project totals", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Preview state", { exact: true })
    .selectOption("Loading");
  await expect(
    page.getByRole("heading", { name: "Loading workspace…", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Preview state", { exact: true }).selectOption("Ready");
  await nav(page, "Activity").click();
  await page
    .getByLabel("Preview state", { exact: true })
    .selectOption("Disconnected");
  await page.getByRole("button", { name: "Reconnect", exact: true }).click();
  await expect(page.getByLabel("Preview state", { exact: true })).toHaveValue(
    "Ready",
  );
  await page.goto("/#/documents/doc-mcp");
  await page
    .getByRole("button", { name: "Edit document", exact: true })
    .click();
  await page
    .getByLabel("Document content", { exact: true })
    .fill("My unsaved draft");
  await page
    .getByLabel("Preview state", { exact: true })
    .selectOption("Conflict");
  await page
    .getByRole("button", { name: "Save document", exact: true })
    .click();
  await expect(
    page.getByLabel("Document content", { exact: true }),
  ).toHaveValue("My unsaved draft");
  await expect(page.locator(".conflict-panel")).toContainText(
    "Current saved content",
  );
});

test("desktop responsive layouts and control focus stay contained", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  for (const width of [1600, 1280, 900]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/#/tickets");
    await page.getByRole("button", { name: "▥ Board", exact: true }).focus();
    await page.keyboard.press("Tab");
    const style = await page
      .getByLabel("Filter tickets by status")
      .evaluate((e) => {
        const s = getComputedStyle(e);
        return {
          outline: s.outlineStyle,
          shadow: s.boxShadow,
          padding: parseInt(s.paddingRight),
          position: s.backgroundPosition,
          focused: document.activeElement === e,
        };
      });
    expect(style.focused).toBe(true);
    expect(style.outline).toBe("none");
    expect(style.shadow).toContain("inset");
    expect(style.padding).toBeGreaterThanOrEqual(32);
    expect(style.position).toContain("10px");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.goto("/#/documents/doc-mcp/history");
    await expect(
      page.getByRole("heading", { name: "Revision history", exact: true }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  expect(errors).toEqual([]);
});

test("native modal keeps page inert, restores invoker focus and has contrasting internal focus", async ({
  page,
}) => {
  await page.goto("/#/projects");
  await page.getByRole("button", { name: "New project", exact: true }).click();
  const save = modal(page).getByRole("button", {
    name: "Create project",
    exact: true,
  });
  const close = modal(page).getByRole("button", {
    name: "Close dialog",
    exact: true,
  });
  await save.focus();
  await page.keyboard.press("Tab");
  expect(
    await page.evaluate(
      () =>
        document.activeElement === document.body ||
        !!document.querySelector("dialog")?.contains(document.activeElement),
    ),
  ).toBe(true);
  await page.keyboard.press("Shift+Tab");
  expect(
    await page.evaluate(
      () =>
        document.activeElement === document.body ||
        !!document.querySelector("dialog")?.contains(document.activeElement),
    ),
  ).toBe(true);
  await save.focus();
  const focus = await save.evaluate((e) => ({
    shadow: getComputedStyle(e).boxShadow,
    background: getComputedStyle(e).backgroundColor,
  }));
  expect(focus.shadow).toContain("inset");
  expect(focus.shadow).toContain("255, 255, 255");
  expect(focus.background).not.toBe("rgb(255, 255, 255)");
  await close.click();
  await expect(
    page.getByRole("button", { name: "New project", exact: true }),
  ).toBeFocused();
});
