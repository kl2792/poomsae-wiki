import { test, expect } from "@playwright/test";

test.describe("Technique detail page", () => {
  test("low-block page renders", async ({ page }) => {
    await page.goto("techniques/low-block");
    await expect(page.getByRole("heading", { name: "Low Block" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Used in" })).toBeVisible();
  });

  test("back link returns to techniques wiki", async ({ page }) => {
    await page.goto("techniques/low-block");
    await page.getByRole("link", { name: /All techniques/ }).click();
    await expect(page).toHaveURL(/\/techniques$/);
  });

  test("used-in form pill links to form", async ({ page }) => {
    await page.goto("techniques/low-block");
    const formLink = page.locator('a[href*="/forms/taegeuk-1"]').first();
    await formLink.click();
    await expect(page).toHaveURL(/\/forms\/taegeuk-1/);
  });

  test("combo technique page shows components", async ({ page }) => {
    await page.goto("techniques/front-kick--plus--middle-punch");
    await expect(page.getByRole("heading", { name: "Components" })).toBeVisible();
  });

  test("unknown technique key returns 404", async ({ page }) => {
    const res = await page.goto("techniques/totally-fake-key-xyz");
    expect(res?.status()).toBe(404);
  });
});

test.describe("Scoring page", () => {
  test("renders scoring breakdown", async ({ page }) => {
    await page.goto("scoring");
    await expect(page.getByRole("heading", { name: "Poomsae Scoring" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Accuracy" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Presentation" })).toBeVisible();
  });
});
