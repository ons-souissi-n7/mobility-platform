/**
 * Test E2E — Scénarios métier complémentaires (admin)
 * Type : Système / Fonctionnel / Bout-en-bout
 *
 * Comble les manques identifiés dans la matrice de couverture E2E (chapitre 6
 * du rapport) : chaque describe ci-dessous correspond à une ligne marquée
 * "aucun scénario identifié" ou "navigation seule, sans scénario complet" :
 *
 *   ✓ Validation ou rejet d'une mobilité complémentaire (admin)
 *   ✓ Import Excel réel (mobilités entrantes) — vrai dépôt de fichier
 *   ✓ Export CTI — téléchargement réel depuis le navigateur
 *   ✓ Tableaux de bord analytiques — interaction avec les filtres
 *   ✓ Stages internationaux — scénario métier complet (création)
 *   ✓ Contrôle d'accès par rôle — réciproque (admin → espace étudiant)
 */

import { test, expect } from "@playwright/test";
import {
  apiGet,
  apiPostMultipart,
  getReferenceFixtures,
  getUsableAcademicYear,
} from "./helpers";
import { buildIncomingXlsx } from "./excel-builder";

// ══════════════════════════════════════════════════════════════════════════
// VALIDATION / REJET D'UNE MOBILITÉ COMPLÉMENTAIRE
// ══════════════════════════════════════════════════════════════════════════

test.describe("Validation et rejet d'une mobilité complémentaire (admin)", () => {
  // INE fixe fourni par le mock fake-cas (voir fake-cas/users.json) — le
  // Student correspondant est déjà présent en base une fois qu'une synchronisation
  // Pégase a tourné dans la campagne de tests (cf. seedGpaAndQuotas ailleurs
  // dans la suite).
  const STUDENT_INE = "203EA05FISA";

  async function declarePendingMobility(
    page: import("@playwright/test").Page,
  ): Promise<{ id: number; studentName: string }> {
    const year = await getUsableAcademicYear(page);
    const countries = await apiGet<Array<{ id: number; name_fr: string }>>(
      page,
      "/complementary/countries/",
    );
    if (!countries.length) {
      throw new Error("Aucun pays disponible pour déclarer une mobilité complémentaire.");
    }
    const file = Buffer.from("%PDF-1.4 justificatif de test E2E");
    const params = new URLSearchParams({
      academic_year_id: String(year.id),
      experience_type: "Summer school",
      country_id: String(countries[0].id),
      destination_institution: "Université de test E2E",
      start_date: "2026-07-01",
      end_date: "2026-07-15",
    });
    const created = await apiPostMultipart<{
      id: number;
      student_first_name: string;
      student_last_name: string;
    }>(
      page,
      `/complementary/student/${STUDENT_INE}/?${params.toString()}`,
      { name: "justificatif.pdf", mimeType: "application/pdf", buffer: file },
    );
    return {
      id: created.id,
      studentName: `${created.student_last_name} ${created.student_first_name}`,
    };
  }

  test("Un admin valide une mobilité complémentaire en attente", async ({ page }) => {
    const { studentName } = await declarePendingMobility(page);

    await page.goto("/admin/mobilites-complementaires");
    await page.waitForLoadState("networkidle");

    const row = page.locator("tr", { hasText: studentName }).first();
    await expect(row).toBeVisible({ timeout: 10_000 });

    await row.getByRole("button", { name: "Valider" }).click();
    await expect(page.getByText(/Confirmer : Valider/i)).toBeVisible({ timeout: 5_000 });
    await page.getByRole("button", { name: "Valider", exact: true }).last().click();

    await expect(row.getByText(/validé/i)).toBeVisible({ timeout: 10_000 });
  });

  test("Un admin rejette une mobilité complémentaire avec un motif obligatoire", async ({
    page,
  }) => {
    const { studentName } = await declarePendingMobility(page);

    await page.goto("/admin/mobilites-complementaires");
    await page.waitForLoadState("networkidle");

    const row = page.locator("tr", { hasText: studentName }).first();
    await expect(row).toBeVisible({ timeout: 10_000 });

    await row.getByRole("button", { name: "Rejeter" }).click();
    await expect(page.getByText("Rejeter la demande")).toBeVisible({ timeout: 5_000 });

    // Le motif est obligatoire : le bouton Rejeter du formulaire reste désactivé sans texte
    const submitBtn = page.getByRole("button", { name: "Rejeter", exact: true }).last();
    await expect(submitBtn).toBeDisabled();

    await page.getByPlaceholder("Indiquez le motif du rejet…").fill(
      "Justificatif insuffisant — test E2E.",
    );
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    await expect(page.getByText("Rejeter la demande")).not.toBeVisible({ timeout: 10_000 });
    await expect(row.getByText(/rejeté/i)).toBeVisible({ timeout: 10_000 });
    await expect(row.getByText(/Justificatif insuffisant/i)).toBeVisible();
  });
});

// ══════════════════════════════════════════════════════════════════════════
// IMPORT EXCEL RÉEL — MOBILITÉS ENTRANTES
// ══════════════════════════════════════════════════════════════════════════

test.describe("Import Excel réel — mobilités entrantes", () => {
  test("Déposer un fichier .xlsx valide crée bien un étudiant entrant", async ({ page }) => {
    const year = await getUsableAcademicYear(page);
    const ref = await getReferenceFixtures(page);
    const uniqueLastName = `E2EIMPORT${Date.now().toString(36).toUpperCase()}`;

    const buffer = await buildIncomingXlsx({
      DEPARTEMENT: ref.departmentCode,
      CIVILITE: "Mme",
      NOM: uniqueLastName,
      PRENOM: "Test",
      PAYS: ref.countryNameFr,
      "UNIV ORIGINE": ref.universityName,
      "DATE NAISSANCE": "15/06/2001",
      CADRE: ref.categoryName,
      MAIL: "test.e2e.import@example.com",
      "MAIL ENSEEIHT": "test.e2e.import@etu.inp-n7.fr",
      DUREE: "6 mois",
      ANNEE: ref.levelCode,
      PARCOURS: ref.parcoursCode,
    });

    await page.goto("/admin/entrantes");
    await page.waitForLoadState("networkidle");

    // Sélectionner l'année académique cible avant l'import
    const yearSelect = page.getByRole("combobox").first();
    if (await yearSelect.isVisible().catch(() => false)) {
      await yearSelect.selectOption(String(year.id)).catch(() => {});
    }

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: "import-e2e.xlsx",
      mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      buffer,
    });

    // L'import est traité en tâche de fond (Django-Q2) — le frontend attend
    // ~3s avant de rafraîchir le tableau (voir handleImport, incoming-workspace.tsx).
    await expect(page.getByText(uniqueLastName)).toBeVisible({ timeout: 20_000 });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// EXPORT CTI — TÉLÉCHARGEMENT RÉEL DEPUIS LE NAVIGATEUR
// ══════════════════════════════════════════════════════════════════════════

test.describe("Export du rapport CTI — téléchargement réel", () => {
  test("Cliquer 'Exporter Excel' déclenche un vrai téléchargement de fichier", async ({
    page,
  }) => {
    await page.goto("/admin/statistiques");
    await page.waitForLoadState("networkidle");

    const exportBtn = page.getByRole("button", { name: "Exporter Excel" });
    await expect(exportBtn).toBeVisible({ timeout: 10_000 });

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      exportBtn.click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
    const path = await download.path();
    expect(path).toBeTruthy();
  });
});

// ══════════════════════════════════════════════════════════════════════════
// TABLEAUX DE BORD ANALYTIQUES — INTERACTION AVEC LES FILTRES
// ══════════════════════════════════════════════════════════════════════════

test.describe("Tableaux de bord analytiques — filtres", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin/analytiques");
    await page.waitForLoadState("networkidle");
  });

  test("Le panneau 'Filtrer' des départements s'ouvre et propose des options", async ({
    page,
  }) => {
    // Le filtre "Filtrer les départements…" n'est rendu que sous l'onglet
    // "Par département" (AnalyticsDashboard.activeTab, défaut "global").
    await page.getByRole("button", { name: "Par département" }).click();

    const filterButtons = page.getByRole("button", { name: /filtrer/i });
    await expect(filterButtons.first()).toBeVisible({ timeout: 10_000 });
    await filterButtons.first().click();

    // Une liste d'options à cocher doit apparaître
    await expect(page.getByRole("checkbox").first()).toBeVisible({ timeout: 5_000 });
  });

  test("Sélectionner un filtre département fait apparaître un badge de comptage", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Par département" }).click();

    const filterButtons = page.getByRole("button", { name: /filtrer/i });
    await expect(filterButtons.first()).toBeVisible({ timeout: 10_000 });
    await filterButtons.first().click();

    const firstOption = page.getByRole("checkbox").first();
    await expect(firstOption).toBeVisible({ timeout: 5_000 });
    await firstOption.check();

    // Le bouton "Filtrer" affiche un badge "1" une fois une option sélectionnée
    await expect(filterButtons.first().getByText("1", { exact: true })).toBeVisible({
      timeout: 5_000,
    });
  });

  test("Le graphique d'évolution des flux affiche des données (SVG Recharts)", async ({
    page,
  }) => {
    await expect(
      page.getByRole("heading", { name: "Évolution des flux de mobilité" }),
    ).toBeVisible({
      timeout: 10_000,
    });
    // Recharts rend un <svg> avec des chemins/barres dès que les données arrivent
    const chartSvg = page.locator("svg.recharts-surface").first();
    await expect(chartSvg).toBeVisible({ timeout: 10_000 });
  });

  test("L'export analytique déclenche un vrai téléchargement", async ({ page }) => {
    const exportBtn = page.getByRole("button", { name: "Exporter Excel" });
    await expect(exportBtn).toBeVisible({ timeout: 10_000 });

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      exportBtn.click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
  });
});

// ══════════════════════════════════════════════════════════════════════════
// STAGES INTERNATIONAUX — SCÉNARIO MÉTIER COMPLET
// ══════════════════════════════════════════════════════════════════════════

test.describe("Stages internationaux — création complète", () => {
  test("Un admin crée un stage international rattaché à un étudiant existant", async ({
    page,
  }) => {
    const students = await apiGet<{ results: Array<{ id: number; first_name: string; last_name: string }> }>(
      page,
      "/students/students/?page_size=1",
    );
    if (!students.results.length) {
      test.skip(true, "Aucun étudiant en base pour rattacher un stage — préconditions absentes.");
      return;
    }
    const student = students.results[0];
    const companyName = `E2E-Entreprise-${Date.now().toString(36)}`;

    await page.goto("/admin/internships");
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "Ajouter" }).click();
    const modalTitle = page.getByRole("heading", { name: "Nouveau stage" });
    await expect(modalTitle).toBeVisible({ timeout: 5_000 });

    await page.locator('input[placeholder*="INE"]').fill(String(student.id));
    await expect(page.getByText(`ID étudiant : ${student.id}`)).toBeVisible();

    await page.locator('input[name="company_name"]').fill(companyName);
    await page.locator('input[name="city"]').fill("Toulouse");
    await page.locator('select[name="internship_type"]').selectOption("Stage 3A");
    await page.locator('input[name="start_date"]').fill("2026-06-01");
    await page.locator('input[name="end_date"]').fill("2026-08-31");

    await page.getByRole("button", { name: "Enregistrer" }).click();

    await expect(modalTitle).not.toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(companyName)).toBeVisible({ timeout: 10_000 });
  });
});

// ══════════════════════════════════════════════════════════════════════════
// CONTRÔLE D'ACCÈS PAR RÔLE — RÉCIPROQUE (ADMIN → ESPACE ÉTUDIANT)
// ══════════════════════════════════════════════════════════════════════════

test.describe("Contrôle d'accès par rôle — admin vers espace étudiant", () => {
  test("Un admin est redirigé hors de l'espace étudiant (toutes les routes /student/*)", async ({
    page,
  }) => {
    const studentRoutes = [
      "/student/tableau-de-bord",
      "/student/accords",
      "/student/mobilite",
      "/student/mobilite-complementaire",
      "/student/recommandations",
    ];
    for (const route of studentRoutes) {
      await page.goto(route);
      await expect(page).not.toHaveURL(new RegExp(route), { timeout: 10_000 });
      await expect(page).toHaveURL(/\/admin\//, { timeout: 10_000 });
    }
  });
});
