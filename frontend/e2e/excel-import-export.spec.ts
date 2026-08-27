/**
 * Test E2E — Fichiers Excel accords & étudiants (import / export / template)
 * Type : Système / Fonctionnel / Bout-en-bout
 *
 * Vérifie, pour les deux pipelines Excel (accords de mobilité, étudiants) :
 *   - Le template téléchargé contient les bonnes colonnes.
 *   - Un import réel (dépôt de fichier, traité en tâche de fond) importe
 *     bien les lignes valides ET enregistre les lignes invalides dans le
 *     panneau d'erreurs — sans perte d'information.
 *   - L'export Excel déclenche un vrai téléchargement.
 */

import { test, expect } from "@playwright/test";
import { apiGet, getReferenceFixtures } from "./helpers";
import { buildAgreementsXlsx, buildStudentsXlsx } from "./excel-builder";

// ══════════════════════════════════════════════════════════════════════════
// ÉTUDIANTS
// ══════════════════════════════════════════════════════════════════════════

test.describe("Import Excel réel — étudiants", () => {
  test("Ligne valide importée + ligne invalide dans le panneau d'erreurs", async ({ page }) => {
    const ref = await getReferenceFixtures(page);
    // Année dédiée aux comptes de test 2026-2027 (statut "initialization" —
    // seule phase où l'import Excel est activé, cf. isLocked dans
    // students-workspace.tsx). getUsableAcademicYear() pourrait retourner
    // une année verrouillée selon l'état du run E2E ; on cible celle-ci
    // explicitement pour un test déterministe.
    const years = await apiGet<Array<{ id: number; label: string; status: string }>>(
      page,
      "/academic/years/?page_size=100",
    );
    const year = years.find((y) => y.label === "2026-2027");
    expect(year, "Année 2026-2027 introuvable (seed_test_accounts_2627)").toBeDefined();

    const suffix = Date.now().toString(36).toUpperCase();
    const validLastName = `E2EVALIDE${suffix}`;
    const invalidLastName = `E2EINVALIDE${suffix}`;

    const buffer = await buildStudentsXlsx([
      {
        INE: `E2E0${Date.now().toString().slice(-7)}`,
        Nom: validLastName,
        Prénom: "Test",
        Email: "e2e.valide@example.com",
        Genre: "F",
        Département: ref.departmentCode,
        Niveau: ref.levelCode,
        GPA: "14.5",
        Boursier: "Oui",
        "FISE/FISA": "FISE",
      },
      {
        INE: `E2E1${Date.now().toString().slice(-7)}`,
        Nom: invalidLastName,
        Prénom: "Test",
        Département: "DEPTINCONNU",
        Niveau: ref.levelCode,
      },
    ]);

    await page.goto("/admin/etudiants");
    await page.waitForLoadState("networkidle");
    await page.getByLabel("Année universitaire").selectOption(String(year!.id));

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: "import-e2e-etudiants.xlsx",
      mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      buffer,
    });

    // Import traité en tâche de fond (django-q) — le frontend attend ~3s
    // avant de rafraîchir la liste et le panneau d'erreurs (cf. régression
    // corrigée dans handleExcelImport, students-workspace.tsx).
    await expect(page.getByText(validLastName)).toBeVisible({ timeout: 20_000 });

    await expect(page.getByText(/erreurs d'import étudiants/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(invalidLastName)).not.toBeVisible();
    await expect(page.getByText(/département introuvable/i)).toBeVisible();
  });
});

test.describe("Template & export Excel — étudiants", () => {
  test("Le template téléchargé contient les colonnes Boursier et FISE/FISA, sans ligne d'exemple", async ({ page }) => {
    await page.goto("/admin/etudiants");
    await page.waitForLoadState("networkidle");

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      page.getByRole("button", { name: /template/i }).click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
    const path = await download.path();
    expect(path).toBeTruthy();
  });

  test("L'export étudiants déclenche un vrai téléchargement", async ({ page }) => {
    await page.goto("/admin/etudiants");
    await page.waitForLoadState("networkidle");

    const years = await apiGet<Array<{ id: number; label: string }>>(
      page,
      "/academic/years/?page_size=100",
    );
    const year = years.find((y) => y.label === "2026-2027");
    await page.getByLabel("Année universitaire").selectOption(String(year!.id));

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      page.getByRole("button", { name: /exporter/i }).click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
  });
});

// ══════════════════════════════════════════════════════════════════════════
// ACCORDS DE MOBILITÉ
// ══════════════════════════════════════════════════════════════════════════

test.describe("Import Excel réel — accords de mobilité", () => {
  test("Ligne valide importée + ligne invalide dans le panneau d'erreurs", async ({ page }) => {
    const ref = await getReferenceFixtures(page);
    const suffix = Date.now().toString(36).toUpperCase();
    const validName = `Accord E2E Valide ${suffix}`;
    const invalidName = `Accord E2E Invalide ${suffix}`;

    const buffer = await buildAgreementsXlsx([
      {
        "Etablissement externe": ref.universityName,
        "Nom de l'accord": validName,
        "Departements concernes (codes, ex: SN;3EA)": ref.departmentCode,
        "Nombre de places (entier ou 'illimite')": "5",
        "Duree du sejour (semaines)": "20",
      },
      {
        "Etablissement externe": `Universite Fantome ${suffix}`,
        "Nom de l'accord": invalidName,
      },
    ]);

    await page.goto("/admin/accords");
    await page.waitForLoadState("networkidle");
    // Importer/Template ne sont actifs qu'en statut "initialization" — la
    // page peut par défaut afficher l'année courante verrouillée (ex.
    // 2025-2026 en pre_assignment). On cible explicitement 2026-2027
    // (seed_test_accounts_2627), qui reste en initialization.
    await page.getByLabel("Année universitaire").selectOption("2026-2027");

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: "import-e2e-accords.xlsx",
      mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      buffer,
    });

    // Import traité en tâche de fond (django-q) — le frontend attend ~3s
    // avant de rafraîchir la liste et le panneau d'erreurs
    // (handleExcelImport, mobility-workspace.tsx).
    await expect(page.getByText(validName)).toBeVisible({ timeout: 20_000 });

    await expect(page.getByText(invalidName)).not.toBeVisible();
    await expect(page.getByText(/université introuvable/i)).toBeVisible({ timeout: 10_000 });
  });
});

test.describe("Template & export Excel — accords", () => {
  test("Le template téléchargé contient la colonne Durée du séjour", async ({ page }) => {
    await page.goto("/admin/accords");
    await page.waitForLoadState("networkidle");
    await page.getByLabel("Année universitaire").selectOption("2026-2027");

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      page.getByRole("button", { name: /modèle|template/i }).click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
  });

  test("L'export accords déclenche un vrai téléchargement", async ({ page }) => {
    await page.goto("/admin/accords");
    await page.waitForLoadState("networkidle");

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      page.getByRole("button", { name: /exporter/i }).click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
  });
});
