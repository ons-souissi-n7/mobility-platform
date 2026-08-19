/**
 * Setup global Playwright — exécuté UNE FOIS avant tous les tests.
 *
 * Effectue la connexion CAS pour chaque rôle et sauvegarde l'état du
 * navigateur (cookies auth_token) dans des fichiers JSON réutilisables
 * par chaque projet Playwright.
 *
 * Flux CAS complet :
 *   /login (Next.js) → 600 ms → /auth/login/ (Django)
 *   → /cas/login (fake-cas) → form submit
 *   → /auth/cas-callback/?ticket=... (Django)
 *   → /auth/callback?token=JWT (Next.js)
 *   → cookie auth_token posé → redirect vers /admin ou /student
 */

import { chromium, type FullConfig } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:3000";

interface CasCredentials {
  username: string;
  password: string;
  authFile: string;
  expectedUrlPattern: RegExp;
}

// Identifiants du serveur fake-cas (mock local, cf. fake-cas/users.json) — pas
// de secret réel, mais surchargeables via env pour les environnements CI/E2E.
const ACCOUNTS: CasCredentials[] = [
  {
    username: process.env.E2E_ADMIN_USERNAME ?? "admin@n7.fr",
    password: process.env.E2E_ADMIN_PASSWORD ?? "admin123", // NOSONAR (S6418) — identifiant du mock fake-cas, pas un secret réel
    authFile: "e2e/.auth/admin.json",
    // Matcher sur le chemin uniquement — fonctionne avec localhost ET les noms Docker
    expectedUrlPattern: /\/admin\//,
  },
  {
    username: process.env.E2E_STUDENT_USERNAME ?? "etudiant@etud.n7.fr",
    password: process.env.E2E_STUDENT_PASSWORD ?? "etudiant123", // NOSONAR (S6418) — identifiant du mock fake-cas, pas un secret réel
    authFile: "e2e/.auth/student.json",
    expectedUrlPattern: /\/student\//,
  },
];

async function loginViaCas(
  browser: Awaited<ReturnType<typeof chromium.launch>>,
  creds: CasCredentials,
): Promise<void> {
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Naviguer vers /login — le JS redirige vers CAS après 600 ms
    await page.goto(`${BASE_URL}/login`);

    // Attendre la redirection vers le formulaire CAS — généreux comme le wait
    // ci-dessous : /login est lui aussi compilé à froid par Next.js en mode
    // dev (observé : ~8s de compilation à elle seule sur un premier démarrage,
    // avant même le setTimeout(600ms) et les deux sauts réseau login→backend
    // →fake-cas), et ce budget est d'autant plus serré quand toutes les images
    // sont reconstruites en parallèle (`docker compose ... up --build`).
    await page.waitForURL(/\/cas\/login/, { timeout: 45_000 });

    // Remplir les identifiants CAS
    await page.fill('[name="username"]', creds.username);
    await page.fill('[name="password"]', creds.password);
    await page.click('[type="submit"]');

    // Attendre le retour sur l'application Next.js — généreux car en mode dev
    // Next.js compile les routes à la demande (première visite de /admin/analytiques
    // avec recharts notamment), ce qui peut dépasser 25 s à froid.
    await page.waitForURL(creds.expectedUrlPattern, { timeout: 60_000 });

    // Vérifier que le cookie auth_token est bien posé
    const cookies = await context.cookies(BASE_URL);
    const authCookie = cookies.find((c) => c.name === "auth_token");
    if (!authCookie?.value) {
      throw new Error(
        `Cookie auth_token manquant après la connexion de ${creds.username}`,
      );
    }

    // Sauvegarder l'état du navigateur (cookies + localStorage)
    fs.mkdirSync(path.dirname(creds.authFile), { recursive: true });
    await context.storageState({ path: creds.authFile });

    console.log(`✓ Auth state sauvegardé pour ${creds.username} → ${creds.authFile}`);
  } finally {
    await context.close();
  }
}

export default async function globalSetup(_config: FullConfig): Promise<void> {
  const browser = await chromium.launch({
    // Requis dans certains environnements Docker sans sandbox noyau
    args: process.env.CI ? ["--no-sandbox", "--disable-setuid-sandbox"] : [],
  });

  try {
    for (const account of ACCOUNTS) {
      await loginViaCas(browser, account);
    }
  } finally {
    await browser.close();
  }
}
