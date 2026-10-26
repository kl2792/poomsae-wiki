import { test, expect } from "./fixtures";

const FORMS = [
  "taegeuk-1", "taegeuk-2", "taegeuk-3", "taegeuk-4",
  "taegeuk-5", "taegeuk-6", "taegeuk-7", "taegeuk-8",
  "koryo", "keumgang", "taebaek", "pyeongwon",
  "sipjin", "jitae", "chonkwon", "hansu", "ilyeo",
];

test.describe("Form detail — every form loads", () => {
  for (const form of FORMS) {
    test(`${form} page renders without error`, async ({ page }) => {
      const errors: string[] = [];
      page.on("pageerror", (e) => errors.push(e.message));
      await page.goto(`/forms/${form}`);
      await expect(page.locator("h1")).toBeVisible();
      await expect(page.getByRole("button", { name: /Sequence \(\d+\)/ })).toBeVisible();
      await expect(page.getByRole("button", { name: /Techniques \(\d+\)/ })).toBeVisible();
      expect(errors, `Console errors: ${errors.join("\n")}`).toEqual([]);
    });
  }
});

test.describe("Form detail — interactions (taegeuk-1)", () => {
  test("tab switches between sequence and techniques", async ({ page }) => {
    await page.goto("forms/taegeuk-1");
    const techBtn = page.getByRole("button", { name: /Techniques \(\d+\)/ });
    await techBtn.click();
    await expect(page).toHaveURL(/[?&]tab=techniques/);
    await page.getByRole("button", { name: /Sequence \(\d+\)/ }).click();
    await expect(page).not.toHaveURL(/tab=techniques/);
  });

  test("click sequence step enters detail view with URL param", async ({ page }) => {
    await page.goto("forms/taegeuk-1");
    await page.getByRole("button", { name: /^01 / }).click();
    await expect(page).toHaveURL(/[?&]step=\d+/);
    await expect(page.getByRole("button", { name: /Back to list/ })).toBeVisible();
  });

  test("mode toggle updates URL", async ({ page }) => {
    await page.goto("forms/taegeuk-1");
    const stepBtn = page.getByRole("button", { name: /⏸ Step|▶ Flow/ });
    await stepBtn.click();
    await expect(page).toHaveURL(/[?&]mode=flow/);
    await stepBtn.click();
    await expect(page).not.toHaveURL(/mode=flow/);
  });

  test("step URL param pre-selects step on load", async ({ page }) => {
    await page.goto("forms/taegeuk-1?step=1");
    await expect(page.getByRole("button", { name: /Back to list/ })).toBeVisible();
    await expect(page.getByText(/Step 1/)).toBeVisible();
  });

  test("prev/next navigation updates URL step param", async ({ page }) => {
    await page.goto("forms/taegeuk-1?step=2");
    await expect(page.getByText(/Step 2/).first()).toBeVisible();
    await page.getByRole("button", { name: "◀ Prev" }).click();
    await expect(page).toHaveURL(/[?&]step=1/);
    await page.getByRole("button", { name: "Next ▶" }).click();
    await page.getByRole("button", { name: "Next ▶" }).click();
    await expect(page).toHaveURL(/[?&]step=3/);
  });

  test("back to list clears step param", async ({ page }) => {
    await page.goto("forms/taegeuk-1?step=1");
    await page.getByRole("button", { name: /Back to list/ }).click();
    await expect(page).not.toHaveURL(/step=/);
  });

  test("shareable URL preserves tab + step + mode", async ({ page }) => {
    await page.goto("forms/taegeuk-1?tab=techniques&mode=flow");
    await expect(page).toHaveURL(/tab=techniques/);
    await expect(page).toHaveURL(/mode=flow/);
  });

  test("kihap badge shows on kihap steps", async ({ page }) => {
    await page.goto("forms/taegeuk-1?step=18");
    await expect(page.getByText("KIHAP", { exact: true })).toBeVisible();
  });
});

test.describe("Form detail — combo components", () => {
  test("taegeuk-2 combo step shows components section", async ({ page }) => {
    await page.goto("forms/taegeuk-2");
    await page.getByText(/Front Kick \+ High Punch|Front Kick \+ Middle Punch/i).first().click();
    await expect(page.getByText("Components", { exact: false })).toBeVisible();
  });

  test("combo component link navigates to technique wiki", async ({ page }) => {
    await page.goto("forms/taegeuk-2");
    await page.getByText(/Front Kick \+ Middle Punch/i).first().click();
    const componentLink = page.locator('a[href*="/techniques/front-kick"]').first();
    if (await componentLink.count() > 0) {
      await componentLink.click();
      await expect(page).toHaveURL(/\/techniques\/front-kick/);
    }
  });
});
