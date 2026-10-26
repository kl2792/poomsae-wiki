import { test, expect } from "@playwright/test";

test.describe("Techniques wiki page", () => {
  test("renders with search, filters, and rows", async ({ page }) => {
    await page.goto("techniques");
    await expect(page.getByRole("heading", { name: "Techniques" })).toBeVisible();
    await expect(page.getByPlaceholder("Search techniques...")).toBeVisible();
    await expect(page.locator('[data-technique]').first()).toBeVisible();
  });

  test("search filter updates URL and count", async ({ page }) => {
    await page.goto("techniques");
    await page.getByPlaceholder("Search techniques...").fill("low block");
    await expect(page).toHaveURL(/[?&]q=low\+?block|[?&]q=low%20block/);
    await expect(page.getByText(/Showing \d+ of \d+/)).toBeVisible();
  });

  test("category pill toggles URL param", async ({ page }) => {
    await page.goto("techniques");
    await page.getByRole("button", { name: "Blocks", exact: true }).click();
    await expect(page).toHaveURL(/category=block/);
    await page.getByRole("button", { name: "Blocks", exact: true }).click();
    await expect(page).not.toHaveURL(/category=/);
  });

  test("form pill toggles URL param", async ({ page }) => {
    await page.goto("techniques");
    await page.getByRole("button", { name: /^TG1$/ }).click();
    await expect(page).toHaveURL(/form=taegeuk-1/);
  });

  test("clear filters resets URL", async ({ page }) => {
    await page.goto("techniques?q=block&category=block&form=taegeuk-1");
    await expect(page.getByText("Clear filters")).toBeVisible();
    await page.getByText("Clear filters").click();
    await expect(page).not.toHaveURL(/[?&](q|category|form)=/);
  });

  test("pre-filled URL applies filters on load", async ({ page }) => {
    await page.goto("techniques?q=punch");
    const searchInput = page.getByPlaceholder("Search techniques...");
    await expect(searchInput).toHaveValue("punch");
  });

  test("no-video toggle works", async ({ page }) => {
    await page.goto("techniques");
    await page.getByRole("button", { name: /No video/ }).click();
    await expect(page.getByText(/Showing \d+ of \d+/)).toBeVisible();
  });

  test("category collapse toggles visibility", async ({ page }) => {
    await page.goto("techniques");
    const blocksSection = page.locator('[data-category="block"]');
    const blocksBody = page.locator('[data-collapse-body="block"]');
    await expect(blocksBody).toBeVisible();
    await page.locator('[data-collapse-trigger="block"]').click();
    await expect(blocksBody).toBeHidden();
  });

  test("click technique row navigates to detail", async ({ page }) => {
    await page.goto("techniques");
    const firstRow = page.locator('[data-technique]').first();
    const key = await firstRow.getAttribute("data-technique");
    await firstRow.click();
    await expect(page).toHaveURL(new RegExp(`/techniques/${key}$`));
  });
});
