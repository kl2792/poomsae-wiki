import { test, expect } from "@playwright/test";

test.describe("Home page", () => {
  test("renders title and form grids", async ({ page }) => {
    await page.goto("");
    await expect(page.getByRole("heading", { name: "Poomsae Wiki", level: 1 })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Taegeuk Forms" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Dan Forms" })).toBeVisible();
  });

  test("shows all 17 form cards", async ({ page }) => {
    await page.goto("");
    const cards = page.locator('a[href*="/forms/"]');
    await expect(cards).toHaveCount(17);
  });

  test("form card click navigates to form page", async ({ page }) => {
    await page.goto("");
    await page.getByRole("link", { name: /Taegeuk Il Jang/ }).click();
    await expect(page).toHaveURL(/\/forms\/taegeuk-1$/);
  });

  test("header nav links work", async ({ page }) => {
    await page.goto("");
    await page.getByRole("link", { name: "Techniques", exact: true }).first().click();
    await expect(page).toHaveURL(/\/techniques$/);
    await page.getByRole("link", { name: "Scoring" }).click();
    await expect(page).toHaveURL(/\/scoring$/);
    await page.getByRole("link", { name: "Forms" }).click();
    await expect(page).toHaveURL(/\/(poomsae-wiki\/?|)$/);
  });
});
