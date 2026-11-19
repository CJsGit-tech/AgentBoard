import { expect, test } from "@playwright/test";

test.describe("mock dashboard layout regression checks", () => {
  test("Overview completion count drills into the matching Done tickets", async ({
    page,
  }) => {
    await page.goto("/#/overview");

    const completion = page.locator(".completion");
    await expect(completion).toContainText("1");
    await expect(completion).toContainText("/ 6 tickets done");

    await page
      .locator(".status-counts button")
      .filter({ hasText: "Done" })
      .click();
    await expect(page).toHaveURL(/#\/tickets\?status=Done$/);
    await expect(page.getByLabel("Filter tickets by status")).toHaveValue(
      "Done",
    );
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator("tbody tr").first()).toContainText(
      "Define revision retention",
    );
  });

  test("empty project Overview shows its empty state without raw UUIDs", async ({
    page,
  }) => {
    await page.goto("/#/overview");
    await page.getByLabel("Select project", { exact: true }).selectOption("fieldnotes");

    await expect(page.getByRole("heading", { name: "Fieldnotes", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "No tickets yet", exact: true })).toBeVisible();
    await expect(page.getByText("Project totals", { exact: true })).toHaveCount(0);
    const visibleText = await page.locator("body").innerText();
    expect(visibleText).not.toMatch(/\b[\da-f]{8}(?:-[\da-f]{4}){3}-[\da-f]{12}\b/i);
  });

  test("sidebar and dashboard stay within narrow and zoom-equivalent viewports", async ({
    page,
  }) => {
    for (const viewport of [
      { width: 925, height: 764 },
      // A 125% browser zoom exposes roughly this many CSS pixels from 925x764.
      { width: 740, height: 611 },
    ]) {
      await page.setViewportSize(viewport);
      await page.goto("/#/overview");
      await expect(page.getByRole("heading", { name: "Project totals", exact: true })).toBeVisible();

      const bounds = await page.evaluate(() => {
        const sidebar = document.querySelector(".sidebar")!.getBoundingClientRect();
        const main = document.querySelector("main")!.getBoundingClientRect();
        return {
          viewportWidth: window.innerWidth,
          pageWidth: document.documentElement.scrollWidth,
          sidebarLeft: sidebar.left,
          sidebarRight: sidebar.right,
          mainLeft: main.left,
          mainRight: main.right,
        };
      });
      expect(bounds.pageWidth).toBeLessThanOrEqual(bounds.viewportWidth);
      expect(bounds.sidebarLeft).toBeGreaterThanOrEqual(0);
      expect(bounds.sidebarRight).toBeLessThanOrEqual(bounds.viewportWidth);
      expect(bounds.mainLeft).toBeGreaterThanOrEqual(bounds.sidebarRight - 1);
      expect(bounds.mainRight).toBeLessThanOrEqual(bounds.viewportWidth);
    }
  });
});
