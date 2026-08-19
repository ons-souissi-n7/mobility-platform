import { defineConfig, devices } from "@playwright/test";

/**
 * Configuration Playwright — Tests E2E / Système / Acceptation
 *
 * Stack :
 *   - Frontend : Next.js sur http://localhost:3000
 *   - Backend  : Django sur http://localhost:8000
 *   - CAS mock : fake-cas  sur http://localhost:8380
 *
 * Lancement :
 *   npm run test:e2e            → headless, parallèle
 *   npm run test:e2e:headed     → avec fenêtre navigateur
 *   npm run test:e2e:ui         → interface Playwright UI
 *
 * Ou via Docker (voir docker-compose.test.yml) :
 *   docker compose -f docker-compose.dev.yml -f docker-compose.test.yml \
 *     up --build --exit-code-from playwright
 */
export default defineConfig({
  testDir: "./e2e",

  /* Auth setup must run before everything else */
  globalSetup: "./e2e/global-setup.ts",

  /* Aucun parallélisme pour éviter les conflits d'état FSM */
  fullyParallel: false,
  workers: 1,

  /* En CI : 1 retry ; en local : 0 */
  retries: process.env.CI ? 1 : 0,
  forbidOnly: !!process.env.CI,

  reporter: [
    ["html", { open: "never", outputFolder: "playwright-report" }],
    ["list"],
  ],

  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    // En mode CI (Docker) : tout enregistrer pour pouvoir rejouer dans le rapport
    trace: process.env.CI ? "on" : "on-first-retry",
    screenshot: process.env.CI ? "on" : "only-on-failure",
    video: process.env.CI ? "on" : "retain-on-failure",
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  projects: [
    /* Tests admin (lifecycle, workflow, alertes) */
    {
      name: "admin",
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/admin.json",
      },
      testMatch: [
        "**/academic-year-lifecycle.spec.ts",
        "**/admin-workflow.spec.ts",
        "**/alerts.spec.ts",
      ],
    },

    /* Tests étudiant */
    {
      name: "student",
      use: {
        ...devices["Desktop Chrome"],
        storageState: "e2e/.auth/student.json",
      },
      testMatch: ["**/student-workflow.spec.ts"],
    },
  ],
});
