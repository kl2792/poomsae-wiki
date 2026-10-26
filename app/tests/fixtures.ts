import { test as base } from "@playwright/test";

// Block YouTube iframe loads — flaky in headless Chromium and irrelevant to UI behavior tests.
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route("**/*youtube.com/**", (route) => route.abort());
    await page.route("**/*ytimg.com/**", (route) => route.abort());
    await use(page);
  },
});

export { expect } from "@playwright/test";
