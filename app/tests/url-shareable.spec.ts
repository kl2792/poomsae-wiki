import { test, expect } from "@playwright/test";

/**
 * Every stateful interaction should produce a shareable URL.
 * These tests capture the URL after an action, then reload with it
 * and verify the same state is restored.
 */

test.describe("URL shareability — form detail", () => {
  test("tab=techniques round-trip", async ({ page }) => {
    await page.goto("forms/taegeuk-1");
    await page.getByRole("button", { name: /Techniques \(\d+\)/ }).click();
    const url = page.url();
    expect(url).toMatch(/tab=techniques/);

    await page.goto(url);
    await expect(page.getByRole("button", { name: /Techniques \(\d+\)/ }))
      .toHaveClass(/border-blue-600/);
  });

  test("step=N round-trip", async ({ page }) => {
    await page.goto("forms/taegeuk-1?step=5");
    await expect(page.getByText(/Step 5/)).toBeVisible();
    const url = page.url();
    await page.goto("about:blank");
    await page.goto(url);
    await expect(page.getByText(/Step 5/)).toBeVisible();
  });

  test("mode=flow round-trip", async ({ page }) => {
    await page.goto("forms/taegeuk-1?mode=flow");
    await expect(page.getByRole("button", { name: /▶ Flow/ })).toBeVisible();
  });

  test("combined params round-trip", async ({ page }) => {
    // step=3 opens detail view where the mode toggle isn't shown.
    // Test mode=flow separately via list view (no step), then combine tab+step.
    await page.goto("forms/taegeuk-1?step=3&tab=techniques");
    await expect(page.getByText(/Step 3/).first()).toBeVisible();
    await expect(page).toHaveURL(/tab=techniques/);
  });
});

test.describe("URL shareability — techniques wiki", () => {
  test("q= round-trip", async ({ page }) => {
    await page.goto("techniques?q=kick");
    await expect(page.getByPlaceholder("Search techniques...")).toHaveValue("kick");
  });

  test("category= round-trip", async ({ page }) => {
    await page.goto("techniques?category=block");
    await expect(page.getByRole("button", { name: "Blocks", exact: true }))
      .toHaveClass(/bg-gray-800/);
  });

  test("form= round-trip", async ({ page }) => {
    await page.goto("techniques?form=taegeuk-1");
    await expect(page.getByRole("button", { name: /^TG1$/ }))
      .toHaveClass(/bg-gray-800/);
  });

  test("multi-value category= round-trip", async ({ page }) => {
    await page.goto("techniques?category=block,strike");
    await expect(page.getByRole("button", { name: "Blocks", exact: true }))
      .toHaveClass(/bg-gray-800/);
    await expect(page.getByRole("button", { name: "Strikes", exact: true }))
      .toHaveClass(/bg-gray-800/);
  });

  test("combined q+category+form round-trip", async ({ page }) => {
    await page.goto("techniques?q=block&category=block&form=taegeuk-1");
    await expect(page.getByPlaceholder("Search techniques...")).toHaveValue("block");
    await expect(page.getByRole("button", { name: "Blocks", exact: true }))
      .toHaveClass(/bg-gray-800/);
    await expect(page.getByRole("button", { name: /^TG1$/ }))
      .toHaveClass(/bg-gray-800/);
  });
});

test.describe("URL shareability — direct deep links", () => {
  test("direct link to combo technique page", async ({ page }) => {
    await page.goto("techniques/front-kick--plus--middle-punch");
    await expect(page.getByRole("heading", { name: /Front Kick/ })).toBeVisible();
  });

  test("no ?t= on fresh load", async ({ page }) => {
    await page.goto("forms/taegeuk-1");
    expect(page.url()).not.toMatch(/[?&]t=/);
  });
});
