import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  timeout: 30000,
  expect: { timeout: 5000 },
  fullyParallel: false,
  workers: 1,
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile:
          "../docs/designs/screens/evidence/run-001/playwright-results.json",
      },
    ],
  ],
  outputDir: "../docs/designs/screens/evidence/run-001/test-results",
  use: {
    ...devices["Desktop Chrome"],
    channel: "chrome",
    baseURL: "http://127.0.0.1:4203",
    viewport: { width: 1600, height: 1100 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev -- --port 4203",
    url: "http://127.0.0.1:4203",
    reuseExistingServer: true,
  },
});
