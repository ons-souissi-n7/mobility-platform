import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Generated Playwright artifacts (HTML report + traces bundle a minified
    // vendor JS viewer that isn't project source and shouldn't be linted).
    "playwright-report/**",
    "test-results/**",
    // Generated Vitest coverage report (HTML/lcov viewer, not project source).
    "coverage/**",
  ]),
  {
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        destructuredArrayIgnorePattern: "^_",
      }],
      // react-hooks/set-state-in-effect (v7 compiler plugin) rejects the standard
      // "set loading before fetch" pattern; disable until the project migrates to Suspense/use()
      "react-hooks/set-state-in-effect": "off",
    },
  },
]);

export default eslintConfig;
