import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:5080",
    headless: true,
  },
  webServer: {
    command: "powershell -NoProfile -Command \"Set-Location ..; $env:IR_FLOW_NO_BROWSER='1'; $env:IR_FLOW_PORT='5080'; python app.py\"",
    url: "http://127.0.0.1:5080/app/login",
    cwd: ".",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
