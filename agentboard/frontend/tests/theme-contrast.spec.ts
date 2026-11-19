import { test, expect, Locator } from "@playwright/test";

async function contrast(locator: Locator) {
  return locator.evaluate(element => {
    const rgb = (value: string) => (value.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
    const luminance = (color: number[]) => color.map(channel => {
      const value = channel / 255;
      return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
    }).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
    let parent: Element | null = element;
    let background = "rgb(255, 255, 255)";
    while (parent) {
      const candidate = getComputedStyle(parent).backgroundColor;
      if (candidate !== "rgba(0, 0, 0, 0)" && candidate !== "transparent") {
        background = candidate;
        break;
      }
      parent = parent.parentElement;
    }
    const foregroundLight = luminance(rgb(getComputedStyle(element).color));
    const backgroundLight = luminance(rgb(background));
    return (Math.max(foregroundLight, backgroundLight) + 0.05) / (Math.min(foregroundLight, backgroundLight) + 0.05);
  });
}

for (const colorScheme of ["light", "dark"] as const) {
  test.describe(`${colorScheme} theme`, () => {
    test.use({ colorScheme, viewport: { width: 1070, height: 894 } });
    test("navigation, actions, statuses and dialogs keep readable contrast", async ({ page }) => {
      await page.goto("/#/documents");
      const selected = page.locator('.sidebar a[aria-current="page"]');
      expect(await contrast(selected)).toBeGreaterThanOrEqual(4.5);
      const tickets = page.getByRole("navigation", { name: "Project navigation" }).getByRole("link", { name: "Tickets", exact: true });
      await tickets.hover();
      expect(await contrast(tickets)).toBeGreaterThanOrEqual(4.5);
      const create = page.getByRole("button", { name: "New document", exact: true });
      expect(await contrast(create)).toBeGreaterThanOrEqual(4.5);
      await create.click();
      expect(await contrast(page.getByRole("dialog").getByRole("heading"))).toBeGreaterThanOrEqual(4.5);
      await page.keyboard.press("Escape");
      await page.goto("/#/overview");
      for (const status of await page.locator('.status-counts .status').all()) {
        expect(await contrast(status)).toBeGreaterThanOrEqual(4.5);
      }
      await selected.focus();
      await expect(selected).toBeFocused();
      expect(await selected.evaluate(element => getComputedStyle(element).boxShadow)).not.toBe("none");
    });
  });
}
