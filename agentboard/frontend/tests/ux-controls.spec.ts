import { test, expect } from "@playwright/test";

test("Markdown import is a visible keyboard button and validates the selected file", async ({ page }) => {
  await page.goto("/#/documents");
  const button = page.getByRole("button", { name: "Import Markdown", exact: true });
  await button.focus();
  await expect(button).toBeFocused();
  const chooserPromise = page.waitForEvent("filechooser");
  await button.press("Enter");
  const chooser = await chooserPromise;
  await chooser.setFiles({ name: "review.md", mimeType: "text/markdown", buffer: Buffer.from("# Keyboard import\n\nReview before saving.") });
  await expect(page.getByRole("heading", { name: "Review imported document", exact: true })).toBeFocused();
  await expect(page.getByRole("button", { name: "Confirm and import", exact: true })).toBeEnabled();
});

test("invalid estimates identify and focus the field that needs correction", async ({ page }) => {
  await page.goto("/#/tickets");
  await page.getByRole("button", { name: "New ticket", exact: true }).click();
  await page.getByLabel("Ticket title", { exact: true }).fill("Estimate review");
  const estimate = page.getByLabel("Estimate (days)", { exact: true });
  await estimate.fill("-1");
  await page.getByRole("button", { name: "Create ticket", exact: true }).click();
  await expect(estimate).toBeFocused();
  await expect(estimate).toHaveAttribute("aria-invalid", "true");
  await expect(estimate).toHaveAttribute("aria-describedby", "ticketeditor-error");
  await expect(page.getByLabel("Ticket title", { exact: true })).not.toHaveAttribute("aria-describedby", "ticketeditor-error");
  await estimate.fill("1");
  await expect(estimate).toHaveAttribute("aria-invalid", "false");
});

test("already-linked documents give explicit feedback and cannot be submitted twice", async ({ page }) => {
  await page.goto("/#/tickets/8f24c9e7");
  await page.getByRole("combobox", { name: "Link document", exact: true }).selectOption("doc-mcp");
  await expect(page.getByRole("button", { name: "Already linked", exact: true })).toBeDisabled();
  await page.getByRole("combobox", { name: "Document relationship", exact: true }).selectOption("Output");
  await expect(page.getByRole("button", { name: "Link", exact: true })).toBeEnabled();
});


test("ticket drawer moves focus into its form and restores the opener", async ({ page }) => {
  await page.goto("/#/tickets");
  const opener = page.getByRole("button", { name: "New ticket", exact: true });
  await opener.click();
  await expect(page.getByLabel("Ticket title", { exact: true })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(opener).toBeFocused();
});

test("a successful document retry opens the saved document without a discard prompt", async ({ page }) => {
  const discardPrompts: string[] = [];
  page.on("dialog", async dialog => { discardPrompts.push(dialog.message()); await dialog.dismiss(); });
  await page.goto("/#/documents");
  await page.getByRole("button", { name: "New document", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Document title", { exact: true }).fill("Retry navigation check");
  await dialog.getByLabel("Document content", { exact: true }).fill("Saved content stays available after retry.");
  await page.getByLabel("Fail next save").check();
  await dialog.getByRole("button", { name: "Save document", exact: true }).click();
  await expect(dialog.getByRole("alert")).toContainText("Save failed");
  await dialog.getByRole("button", { name: "Save document", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Retry navigation check", exact: true })).toBeVisible();
  expect(discardPrompts).toEqual([]);
});
