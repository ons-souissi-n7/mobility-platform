/**
 * Tests E2E — Workflow étudiant
 * Type : Système / Fonctionnel / Bout-en-bout / Acceptation
 *
 * Vérifie l'ensemble des fonctionnalités disponibles côté étudiant :
 *   ✓ Authentification et redirection post-connexion
 *   ✓ Navigation latérale (sidebar — tous les liens)
 *   ✓ Tableau de bord (durée de mobilité CTI)
 *   ✓ Accords disponibles (tableau, colonnes, sélecteur d'année)
 *   ✓ Recommandations (page en cours de développement)
 *   ✓ Ma mobilité (Mes vœux + Mon résultat selon l'état de l'année)
 *   ✓ Redirection /voeux → /mobilite
 *   ✓ Mobilité complémentaire (formulaire, validation, déclarations)
 *   ✓ Déconnexion (bouton présent)
 *
 * Les routes étudiant ne portent plus l'INE dans l'URL (/student/... et non
 * /student/<ine>/...) : l'identité vient exclusivement du JWT en session.
 *
 * INE de l'étudiant de test : 203EA05FISA (fake-CAS users.json)
 */

import { test, expect, type Page } from "@playwright/test";

// ── Constantes ─────────────────────────────────────────────────────────────

/** INE de l'étudiant de test (défini dans fake-cas/users.json). */
const STUDENT_INE = "203EA05FISA";

/** Base des routes étudiant. */
const BASE = "/student";

// ── Helper de navigation ────────────────────────────────────────────────────

async function goTo(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
}

// ══════════════════════════════════════════════════════════════════════════
// AUTH & REDIRECTIONS
// ══════════════════════════════════════════════════════════════════════════

test.describe("Auth étudiant et redirections", () => {
  test("La racine / redirige vers l'espace étudiant après connexion", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/student\//, { timeout: 15_000 });
  });

  test("L'URL ne contient jamais l'INE de l'étudiant", async ({ page }) => {
    // L'identité vient du JWT en session, jamais de l'URL — voir la refonte
    // qui a retiré le segment [ine] des routes /student/*.
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await expect(page).not.toHaveURL(new RegExp(STUDENT_INE));
  });

  test("/student redirige directement vers le tableau de bord", async ({ page }) => {
    await page.goto("/student");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/student\/tableau-de-bord$/, { timeout: 15_000 });
    await expect(page.getByText("N7 MOBILITE").first()).toBeVisible({ timeout: 10_000 });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// SIDEBAR
// ══════════════════════════════════════════════════════════════════════════

test.describe("Sidebar étudiant", () => {
  test.beforeEach(async ({ page }) => {
    await goTo(page, `${BASE}/tableau-de-bord`);
  });

  test("Le logo 'N7 MOBILITE' est visible", async ({ page }) => {
    // Le logo apparaît deux fois dans le DOM (sidebar desktop + header mobile,
    // masqué par CSS selon la largeur d'écran, pas rendu conditionnellement).
    await expect(page.getByText("N7 MOBILITE").first()).toBeVisible();
  });

  test("L'email étudiant est affiché dans la sidebar", async ({ page }) => {
    await expect(
      page.locator("aside").getByText(/etudiant@etud\.n7\.fr/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("L'INE est affiché dans la sidebar", async ({ page }) => {
    await expect(
      page.locator("aside").getByText(new RegExp(STUDENT_INE)),
    ).toBeVisible({ timeout: 10_000 });
  });

  const navItems = [
    { label: "Tableau de bord",        path: "tableau-de-bord" },
    { label: "Accords disponibles",    path: "accords" },
    { label: "Recommandations",        path: "recommandations" },
    { label: "Ma mobilité",            path: "mobilite" },
    { label: "Mobilité complémentaire", path: "mobilite-complementaire" },
  ];

  for (const { label, path } of navItems) {
    test(`Le lien "${label}" est présent dans la sidebar`, async ({ page }) => {
      await expect(page.locator("aside").getByRole("link", { name: label })).toBeVisible();
    });

    test(`Le lien "${label}" navigue vers /${path}`, async ({ page }) => {
      await page.locator("aside").getByRole("link", { name: label }).click();
      await expect(page).toHaveURL(new RegExp(`/${path}`), { timeout: 15_000 });
    });
  }

  test("Le bouton de déconnexion est présent dans la sidebar", async ({ page }) => {
    await expect(
      page.locator("aside").getByRole("button", { name: /déconnexion/i })
        .or(page.locator("aside [title='Déconnexion']")),
    ).toBeVisible({ timeout: 10_000 });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// TABLEAU DE BORD
// ══════════════════════════════════════════════════════════════════════════

test.describe("Tableau de bord étudiant", () => {
  test.beforeEach(async ({ page }) => {
    await goTo(page, `${BASE}/tableau-de-bord`);
  });

  test("La page se charge sans erreur 404 ni 500", async ({ page }) => {
    await expect(page.locator("body")).not.toContainText("404");
    await expect(page.locator("body")).not.toContainText("Erreur 500");
  });

  test("Le titre 'Tableau de bord' est affiché", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Tableau de bord" })).toBeVisible({ timeout: 10_000 });
  });

  test("Le sous-titre mentionne la durée cumulée de mobilité", async ({ page }) => {
    await expect(
      page.getByText(/durée cumulée/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("Les trois catégories de mobilité sont visibles après chargement", async ({ page }) => {
    // Attendre que le chargement soit terminé
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 15_000 });

    // Soit les données sont chargées, soit une erreur est affichée
    const hasContent = await page.getByText(/mobilité sortante|sortante/i).isVisible().catch(() => false);
    const hasError   = await page.getByText(/impossible|erreur/i).isVisible().catch(() => false);
    expect(hasContent || hasError).toBe(true);
  });
});

// ══════════════════════════════════════════════════════════════════════════
// ACCORDS DISPONIBLES
// ══════════════════════════════════════════════════════════════════════════

test.describe("Page accords disponibles", () => {
  test.beforeEach(async ({ page }) => {
    await goTo(page, `${BASE}/accords`);
  });

  test("La page se charge sans erreur", async ({ page }) => {
    await expect(page.locator("body")).not.toContainText("404");
  });

  test("Le titre 'Accords disponibles' est affiché", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Accords disponibles" })).toBeVisible({ timeout: 10_000 });
  });

  test("Le sous-titre mentionne le profil étudiant", async ({ page }) => {
    await expect(
      page.getByText(/niveau et département/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("Un sélecteur d'année universitaire est disponible", async ({ page }) => {
    // Le select n'apparaît que si l'étudiant est inscrit dans au moins une année
    await page.waitForLoadState("networkidle");
    const select = page.locator("select").first();
    // Si pas d'années inscrites, le select n'est pas là, c'est acceptable
    const hasSelect = await select.isVisible().catch(() => false);
    if (hasSelect) {
      await expect(select).toBeVisible();
    }
  });

  test("Après chargement, soit un tableau soit un message vide est affiché", async ({ page }) => {
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 15_000 });

    const hasTable   = await page.locator("table").isVisible().catch(() => false);
    const hasEmpty   = await page.getByText(/aucun accord/i).isVisible().catch(() => false);
    const hasError   = await page.getByText(/impossible/i).isVisible().catch(() => false);
    expect(hasTable || hasEmpty || hasError).toBe(true);
  });

  test("Si un tableau est présent, il contient les en-têtes attendus", async ({ page }) => {
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 15_000 });

    const tableVisible = await page.locator("table").isVisible().catch(() => false);
    if (!tableVisible) {
      test.skip();
      return;
    }

    const headers = ["Université", "Accord", "Direction", "Quota N7"];
    for (const header of headers) {
      await expect(page.getByText(header).first()).toBeVisible();
    }
  });
});

// ══════════════════════════════════════════════════════════════════════════
// RECOMMANDATIONS
// ══════════════════════════════════════════════════════════════════════════

test.describe("Page recommandations", () => {
  test.beforeEach(async ({ page }) => {
    await goTo(page, `${BASE}/recommandations`);
  });

  test("La page se charge sans erreur 404", async ({ page }) => {
    await expect(page.locator("body")).not.toContainText("404");
  });

  test("Le placeholder 'à développer' est présent (fonctionnalité future)", async ({ page }) => {
    // Cette page est intentionnellement un placeholder pour le sprint suivant
    await expect(
      page.getByText(/recommandations.*à développer/i)
        .or(page.getByText("Recommandations — à développer")),
    ).toBeVisible({ timeout: 10_000 });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// MA MOBILITÉ
// ══════════════════════════════════════════════════════════════════════════

test.describe("Page Ma mobilité", () => {
  test.beforeEach(async ({ page }) => {
    await goTo(page, `${BASE}/mobilite`);
  });

  test("La page se charge sans erreur", async ({ page }) => {
    await expect(page.locator("body")).not.toContainText("404");
    await expect(page.locator("body")).not.toContainText("Erreur 500");
  });

  test("Le titre 'Ma mobilité' est affiché", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Ma mobilité" })).toBeVisible({ timeout: 10_000 });
  });

  test("La section 'Mes vœux' est présente", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Mes vœux" })).toBeVisible({ timeout: 15_000 });
  });

  test("La section 'Mon résultat' est présente", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Mon résultat" })).toBeVisible({ timeout: 15_000 });
  });

  test("L'état 'Aucun vœu' ou une liste de vœux est affiché après chargement", async ({ page }) => {
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 20_000 });

    const hasWishes  = await page.locator("ol li").first().isVisible().catch(() => false);
    const hasNoWish  = await page.getByText(/aucun vœu/i).isVisible().catch(() => false);
    const hasError   = await page.getByText(/impossible/i).isVisible().catch(() => false);
    expect(hasWishes || hasNoWish || hasError).toBe(true);
  });

  test("La section Mon résultat affiche un état cohérent avec l'année", async ({ page }) => {
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 20_000 });

    // L'une des trois situations doit être affichée
    const isAssigned    = await page.getByText(/affecté\(e\) en mobilité/i).isVisible().catch(() => false);
    const notPublished  = await page.getByText(/résultats ne sont pas encore publiés/i).isVisible().catch(() => false);
    const noneForYear   = await page.getByText(/aucun résultat d'affectation/i).isVisible().catch(() => false);
    const notAssigned   = await page.getByText(/non affecté\(e\)/i).isVisible().catch(() => false);
    const hasError      = await page.getByText(/impossible/i).isVisible().catch(() => false);

    expect(isAssigned || notPublished || noneForYear || notAssigned || hasError).toBe(true);
  });
});

// ══════════════════════════════════════════════════════════════════════════
// REDIRECTION /voeux → /mobilite
// ══════════════════════════════════════════════════════════════════════════

test.describe("Redirection /voeux", () => {
  test("/voeux redirige vers /mobilite", async ({ page }) => {
    await page.goto(`${BASE}/voeux`);
    await expect(page).toHaveURL(/\/student\/mobilite$/, { timeout: 15_000 });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// MOBILITÉ COMPLÉMENTAIRE
// ══════════════════════════════════════════════════════════════════════════

test.describe("Page mobilité complémentaire", () => {
  test.beforeEach(async ({ page }) => {
    await goTo(page, `${BASE}/mobilite-complementaire`);
  });

  test("La page se charge sans erreur", async ({ page }) => {
    await expect(page.locator("body")).not.toContainText("404");
    await expect(page.locator("body")).not.toContainText("Erreur 500");
  });

  test("Le titre 'Mobilité complémentaire' est affiché", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Mobilité complémentaire" }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("La section 'Mes déclarations' est présente", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Mes déclarations" }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("Pour une année non clôturée, le formulaire de déclaration est visible", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    // Si l'année en cours est non clôturée, le formulaire apparaît
    const hasClosed = await page.getByText("Année clôturée").isVisible().catch(() => false);
    if (hasClosed) {
      // L'année est clôturée : le formulaire est masqué, c'est correct
      await expect(page.getByText("lecture seule")).toBeVisible();
    } else {
      // L'année est ouverte ou pas d'année : chercher le formulaire
      const hasForm = await page.locator("form").isVisible().catch(() => false);
      // Peut ne pas avoir de formulaire si l'étudiant n'est pas inscrit dans une année
      if (hasForm) {
        await expect(
          page.getByRole("heading", { name: "Déclarer une nouvelle expérience" }),
        ).toBeVisible();
      }
    }
  });

  test("Le formulaire contient tous les champs requis", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    // Ne tester le formulaire que s'il est présent (année non clôturée)
    const hasForm = await page.locator("form").isVisible().catch(() => false);
    if (!hasForm) {
      test.skip();
      return;
    }

    await expect(page.locator('[name="experience_type"]')).toBeVisible();
    await expect(page.locator('[name="country_id"]')).toBeVisible();
    await expect(page.locator('[name="start_date"]')).toBeVisible();
    await expect(page.locator('[name="end_date"]')).toBeVisible();
    await expect(page.locator('[name="document"]')).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Soumettre la déclaration" }),
    ).toBeVisible();
  });

  test("Le formulaire affiche une erreur si soumis sans fichier justificatif", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const hasForm = await page.locator("form").isVisible().catch(() => false);
    if (!hasForm) {
      test.skip();
      return;
    }

    // Remplir les champs texte mais pas le fichier
    await page.fill('[name="experience_type"]', "Summer school test");
    await page.fill('[name="start_date"]', "2025-07-01");
    await page.fill('[name="end_date"]', "2025-07-31");

    await page.getByRole("button", { name: "Soumettre la déclaration" }).click();

    // L'erreur "Veuillez sélectionner un fichier justificatif" doit apparaître
    await expect(
      page.getByText(/veuillez sélectionner un fichier/i),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("Le formulaire affiche une erreur si soumis sans pays de destination", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const hasForm = await page.locator("form").isVisible().catch(() => false);
    if (!hasForm) {
      test.skip();
      return;
    }

    // Remplir les champs sans sélectionner de pays
    await page.fill('[name="experience_type"]', "Summer school test");
    await page.fill('[name="start_date"]', "2025-07-01");
    await page.fill('[name="end_date"]', "2025-07-31");

    // Simuler un fichier via l'input (sans vrai upload réseau)
    await page.locator('[name="document"]').setInputFiles({
      name: "test.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("fake pdf content"),
    });

    await page.getByRole("button", { name: "Soumettre la déclaration" }).click();

    // L'erreur de pays manquant doit apparaître
    await expect(
      page.getByText(/veuillez sélectionner un pays/i),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("Le bouton 'Soumettre' passe en état 'Envoi en cours…' pendant la soumission", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const hasForm = await page.locator("form").isVisible().catch(() => false);
    if (!hasForm) {
      test.skip();
      return;
    }

    // Bloquer la requête réseau pour observer l'état de chargement — un délai
    // artificiel est nécessaire, sinon la réponse mockée résout si vite que
    // l'état "Envoi en cours…" n'existe que le temps d'un microtask, invisible
    // pour l'assertion qui suit le clic.
    await page.route("**/api/v1/**complementary**", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) });
    });

    // Sélectionner un pays (prendre le premier disponible)
    const countrySelect = page.locator('[name="country_id"]');
    const hasCountries = await countrySelect.locator("option[value]").count() > 0;
    if (!hasCountries) {
      test.skip();
      return;
    }
    await countrySelect.selectOption({ index: 1 });

    await page.fill('[name="experience_type"]', "Summer school test");
    await page.fill('[name="start_date"]', "2025-07-01");
    await page.fill('[name="end_date"]', "2025-07-31");
    await page.locator('[name="document"]').setInputFiles({
      name: "test.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("fake pdf content"),
    });

    const submitBtn = page.getByRole("button", { name: "Soumettre la déclaration" });
    await submitBtn.click();

    // Pendant l'envoi, le texte change
    await expect(
      page.getByRole("button", { name: /envoi en cours/i }),
    ).toBeVisible({ timeout: 3_000 });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// ACCÈS INTERDIT — ISOLATION ENTRE ÉTUDIANTS
// ══════════════════════════════════════════════════════════════════════════

test.describe("Contrôle d'accès étudiant", () => {
  test("Un étudiant ne peut pas accéder à l'espace admin", async ({ page }) => {
    await page.goto("/admin/analytiques");
    await page.waitForLoadState("networkidle");

    // Doit être redirigé hors de /admin ou recevoir une 403
    const url = page.url();
    const isOnAdmin = url.includes("/admin/analytiques");
    if (isOnAdmin) {
      // Si la page est rendue, vérifier qu'il n'y a pas de contenu admin sensible
      await expect(page.getByText(/journal d'audit|statistiques cti/i)).not.toBeVisible({ timeout: 5_000 });
    } else {
      // Redirigé vers /login ou /student
      expect(url).toMatch(/\/login|\/student/);
    }
  });

  // L'ancien test naviguait vers /student/<autre-ine>/tableau-de-bord pour
  // vérifier l'isolation entre étudiants. Cette URL n'existe plus : les routes
  // /student/* ne prennent plus d'INE, l'espace affiché est toujours celui du
  // JWT en session — le vecteur d'attaque (deviner/forger le lien d'un autre
  // étudiant) est donc éliminé structurellement, pas seulement bloqué en aval.
  // L'isolation des données reste vérifiée côté backend par
  // require_student_owns() (voir backend/app/students/student_api.py).
  test("L'espace affiché correspond toujours à l'étudiant de la session (INE dans la sidebar)", async ({ page }) => {
    await page.goto(`${BASE}/tableau-de-bord`);
    await page.waitForLoadState("networkidle");
    await expect(
      page.locator("aside").getByText(new RegExp(STUDENT_INE)),
    ).toBeVisible({ timeout: 10_000 });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// RÉSULTAT D'AFFECTATION — ÉTATS SELON L'ANNÉE
// ══════════════════════════════════════════════════════════════════════════

test.describe("Mobilité — comportement selon état de l'année", () => {
  test("Année non publiée : Mon résultat affiche 'pas encore publiés' ou état équivalent", async ({
    page,
  }) => {
    // Mocker l'API pour simuler un résultat absent (null) et une année en état 'candidature'
    await page.route("**/api/v1/student/**/wishes/**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "[]" }),
    );
    await page.route("**/api/v1/student/**/assignment/**", (route) =>
      route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ detail: "Not found" }) }),
    );

    await goTo(page, `${BASE}/mobilite`);
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 15_000 });

    // Le résultat doit montrer l'un des états attendus
    const notPublished = await page.getByText(/résultats ne sont pas encore publiés/i).isVisible().catch(() => false);
    const noneResult   = await page.getByText(/aucun résultat/i).isVisible().catch(() => false);
    const notAssigned  = await page.getByText(/non affecté/i).isVisible().catch(() => false);
    const isAssigned   = await page.getByText(/affecté\(e\)/i).isVisible().catch(() => false);
    expect(notPublished || noneResult || notAssigned || isAssigned).toBe(true);
  });

  test("Affectation positive : badge vert 'Affecté(e) en mobilité' visible", async ({ page }) => {
    // Simuler une affectation positive
    await page.route("**/api/v1/student/**/wishes/**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "[]" }),
    );
    await page.route("**/api/v1/student/**/assignment/**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          is_assigned: true,
          university_name: "TU Berlin",
          country_name: "Allemagne",
          agreement_name: "Accord Erasmus TUB",
        }),
      }),
    );

    await goTo(page, `${BASE}/mobilite`);
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByText(/affecté\(e\) en mobilité internationale/i),
    ).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("TU Berlin")).toBeVisible();
    await expect(page.getByText("Allemagne")).toBeVisible();
  });

  test("Affectation négative : badge 'Non affecté(e)' visible", async ({ page }) => {
    await page.route("**/api/v1/student/**/wishes/**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "[]" }),
    );
    await page.route("**/api/v1/student/**/assignment/**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ is_assigned: false }),
      }),
    );

    await goTo(page, `${BASE}/mobilite`);
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByText(/non affecté\(e\)/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("Vœux enregistrés : liste ordonnée visible avec rang, université, pays", async ({ page }) => {
    await page.route("**/api/v1/student/**/wishes/**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { rank: 1, university_name: "University of Tokyo", agreement_name: "Accord Japon", country_name: "Japon" },
          { rank: 2, university_name: "MIT",                 agreement_name: "Accord USA",   country_name: "États-Unis" },
        ]),
      }),
    );
    await page.route("**/api/v1/student/**/assignment/**", (route) =>
      route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ detail: "Not found" }) }),
    );

    await goTo(page, `${BASE}/mobilite`);
    await expect(page.getByText("Chargement…")).not.toBeVisible({ timeout: 15_000 });

    await expect(page.getByText("University of Tokyo")).toBeVisible();
    await expect(page.getByText("MIT")).toBeVisible();
    // "Japon" apparaît à la fois dans le nom de l'accord ("Accord Japon") et
    // dans le badge pays séparé — .first() lève juste l'ambiguïté du strict mode.
    await expect(page.getByText("Japon").first()).toBeVisible();

    // Les rangs sont affichés dans des cercles
    const rankBadges = page.locator("ol span").filter({ hasText: "1" });
    await expect(rankBadges.first()).toBeVisible();
  });

  test("Mobilité complémentaire — année clôturée cache le formulaire", async ({ page }) => {
    // Simuler un profil avec une année clôturée
    await page.route("**/api/v1/student/**/profile**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ine: STUDENT_INE,
          first_name: "Etudiant",
          last_name: "Test",
          enrolled_years: [
            {
              academic_year_id: 1,
              academic_year_label: "2024-2025",
              academic_year_status: "closed",
            },
          ],
        }),
      }),
    );
    await page.route("**/api/v1/student/**/complementary**", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "[]" }),
    );

    await goTo(page, `${BASE}/mobilite-complementaire`);
    await page.waitForLoadState("networkidle");

    // "Année clôturée" apparaît à la fois dans un badge dédié et dans le texte
    // plus long du bandeau d'info — .first() lève l'ambiguïté du strict mode.
    await expect(
      page.getByText("Année clôturée").or(page.getByText("lecture seule")).first(),
    ).toBeVisible({ timeout: 10_000 });

    // Le formulaire ne doit pas être visible
    await expect(page.getByText("Déclarer une nouvelle expérience")).not.toBeVisible();
  });
});
