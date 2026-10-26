import { defineConfig, devices } from "@playwright/test";

// Serve the static production build by default — much lighter than next dev.
// Override with BASE_URL=http://localhost:3000/poomsae-wiki/ to test against dev server.
// Trailing slash is required so relative goto("/forms/X") resolves under the basePath.
const BASE_URL = process.env.BASE_URL ?? "http://localhost:4321/poomsae-wiki/";

// Worker count: 1 is safest, 2 is reasonable. Override via PW_WORKERS env var.
const WORKERS = Number(process.env.PW_WORKERS ?? 2);

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  retries: 0,
  workers: WORKERS,
  reporter: [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: process.env.BASE_URL
    ? undefined
    : {
        // Static file server on built output — low CPU, no hot-reload overhead.
        // `serve` handles .html fallback for clean URLs (e.g. /forms/x → /forms/x.html)
        command: "npx serve out -l 4321 --no-clipboard",
        url: BASE_URL,
        reuseExistingServer: true,
        timeout: 30000,
      },
});
