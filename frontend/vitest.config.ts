import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // e2e/** contient les specs Playwright — un framework distinct avec sa
    // propre notion de test.describe(), que Vitest ne doit jamais collecter.
    exclude: ["e2e/**", "node_modules/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      // lcov.info est consommé par SonarQube (sonar.javascript.lcov.reportPaths).
      reportsDirectory: "./coverage",
      exclude: [
        "e2e/**",
        "**/*.config.*",
        "**/*.d.ts",
        ".next/**",
        "playwright-report/**",
        "test-results/**",
      ],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
});
