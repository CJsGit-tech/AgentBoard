import { test, expect } from "@playwright/test";

test("inline markdown renders model formatting without treating emphasis as a link", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/#/documents/doc-mcp");
  await page.getByRole("button", { name: "Edit document", exact: true }).click();
  await page.getByLabel("Document content", { exact: true }).fill("**Bold** _emphasis_ `code` [Safe link](https://example.com)\n\n- **Project:** Demo");
  await page.getByRole("button", { name: "Save document", exact: true }).click();
  await expect(page.locator(".document-reading .markdown-body strong").first()).toHaveText("Bold");
  await expect(page.locator(".document-reading .markdown-body em")).toHaveText("emphasis");
  await expect(page.locator(".document-reading .markdown-body code")).toHaveText("code");
  await expect(page.getByRole("link", { name: "Safe link", exact: true })).toHaveAttribute("href", "https://example.com");
  expect(errors).toEqual([]);
});
