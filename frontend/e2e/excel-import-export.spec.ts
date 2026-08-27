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

import ExcelJS from "exceljs";
import { test, expect } from "@playwright/test";
import { apiGet, getReferenceFixtures } from "./helpers";
import { buildAgreementsXlsx, buildStudentsXlsx } from "./excel-builder";

/** En-têtes attendus du template étudiants — cf. `download_student_template`,
 * backend/app/students/api.py. */
const STUDENT_TEMPLATE_HEADERS = [
  "INE",
  "Nom",
  "Prénom",
  "Email",
  "Genre",
  "Département",
  "Niveau",
  "Parcours",
  "GPA",
  "Boursier",
  "FISE/FISA",
  "Nationalité",
];

/** En-têtes attendus du template accords — cf. `TEMPLATE_COLUMNS`,
 * backend/app/mobility/services/excel_importer.py. */
const AGREEMENT_TEMPLATE_HEADERS = [
  "Etablissement externe",
  "Nom de l'accord",
  "Departements concernes (codes, ex: SN;3EA)",
  "Niveaux concernes (codes, ex: 3A;2A)",
  "Cadre d'accord",
  "Nombre de places (entier ou 'illimite')",
  "Etablissements internes (nom court, ex: INP-ENSEEIHT;INP-ENSAT)",
  "Remarques",
  "Duree du sejour (semaines)",
];

/** Lit la première ligne (en-têtes) d'un classeur téléchargé par Playwright. */
async function readHeaderRow(downloadPath: string): Promise<string[]> {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(downloadPath);
  const ws = wb.worksheets[0];
  const row = ws.getRow(1);
  const headers: string[] = [];
  row.eachCell({ includeEmpty: false }, (cell) => {
    headers.push(String(cell.value ?? "").trim());
  });
  return headers;
}

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
    const invalidIne = `E2E1${Date.now().toString().slice(-7)}`;

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
        INE: invalidIne,
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
    // Scopé sur la ligne d'erreur de CE run (via l'INE, unique par exécution)
    // plutôt qu'un texte générique ("Département introuvable: DEPTINCONNU")
    // — ce message est identique à chaque run, donc un run précédent non
    // nettoyé produirait une seconde ligne correspondante et ferait échouer
    // le match en mode strict (locator résolu à plusieurs éléments).
    const invalidRow = page.getByRole("button").filter({ hasText: invalidIne });
    await expect(invalidRow.getByText(/département introuvable/i)).toBeVisible({
      timeout: 10_000,
    });
  });
});

test.describe("Template & export Excel — étudiants", () => {
  test("Le template téléchargé contient toutes les colonnes attendues", async ({ page }) => {
    await page.goto("/admin/etudiants");
    await page.waitForLoadState("networkidle");

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      page.getByRole("button", { name: /template/i }).click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
    const path = await download.path();
    expect(path).toBeTruthy();

    const headers = await readHeaderRow(path!);
    for (const expected of STUDENT_TEMPLATE_HEADERS) {
      expect(headers).toContain(expected);
    }
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

    await page.goto("/admin/mobility");
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
    // Scopé sur la ligne d'erreur de CE run — cf. le même correctif côté
    // étudiants juste au-dessus : un message générique matcherait aussi une
    // ligne d'un run précédent non nettoyé et ferait échouer le match en
    // mode strict. On filtre par `suffix` (pas `invalidName`) : la ligne
    // d'erreur affiche l'identifiant externe ("row_3_Universite Fantome
    // {suffix}"), pas le nom de l'accord — l'échec de résolution
    // d'université survient avant que le nom de l'accord ne soit retenu.
    const invalidRow = page.getByRole("button").filter({ hasText: suffix });
    await expect(invalidRow.getByText(/université introuvable/i)).toBeVisible({
      timeout: 10_000,
    });
  });
});

test.describe("Template & export Excel — accords", () => {
  test("Le template téléchargé contient toutes les colonnes attendues", async ({ page }) => {
    await page.goto("/admin/mobility");
    await page.waitForLoadState("networkidle");
    await page.getByLabel("Année universitaire").selectOption("2026-2027");

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      page.getByRole("button", { name: /modèle|template/i }).click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
    const path = await download.path();
    expect(path).toBeTruthy();

    const headers = await readHeaderRow(path!);
    for (const expected of AGREEMENT_TEMPLATE_HEADERS) {
      expect(headers).toContain(expected);
    }
  });

  test("L'export accords déclenche un vrai téléchargement", async ({ page }) => {
    await page.goto("/admin/mobility");
    await page.waitForLoadState("networkidle");

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 20_000 }),
      page.getByRole("button", { name: /exporter/i }).click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.xlsx$/i);
  });
});
