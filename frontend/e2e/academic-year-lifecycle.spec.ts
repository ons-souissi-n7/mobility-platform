/**
 * Test E2E — Cycle de vie complet d'une année universitaire
 * Type : Système / E2E / Acceptation / Bout-en-bout
 *
 * Couvre TOUS les états FSM, dans l'ordre :
 *   initialization → recommendation → candidature → import
 *   → pre_assignment → validation → published → finalization → closed
 *
 * Vérifie à chaque état :
 *   ✓ Badge de statut correct
 *   ✓ Bouton de transition présent et actif
 *   ✓ Boutons Modifier / Supprimer enabled ou disabled selon les règles métier
 *   ✓ Dialogue de confirmation (titre, message, bouton confirmer, bouton annuler)
 *   ✓ Pas d'éléments parasites (spinner, Récupérer, tiret) aux mauvais états
 *   ✓ Spinner + bouton "Récupérer" uniquement en pre_assignment
 *   ✓ Message irréversible sur la transition de clôture
 *   ✓ Initialisation de l'année suivante possible après clôture
 *
 * Prérequis :
 *   - Stack lancée (Next.js :3000, Django :8000, fake-CAS :8380)
 *   - Auth admin sauvegardée par global-setup.ts
 *   - `test:e2e:headed` pour visualiser l'exécution
 */

import { test, expect } from "@playwright/test";
import {
  yearRow,
  confirmAction,
  cancelConfirmDialog,
  waitForStatusInRow,
  performTransition,
  getAuthToken,
  seedGpaAndQuotas,
  deleteAgreementYearsForLabel,
  API_BASE,
} from "./helpers";

// ── Données du test ────────────────────────────────────────────────────────

// Label unique pour éviter les collisions entre exécutions
// (limité à 20 caractères côté backend — AcademicYear.label) et doit commencer
// par une année à 4 chiffres suivie d'un tiret : run_sync_pegase_students
// (voir seedGpaAndQuotas) dérive la plage de synchronisation de ce préfixe.
const RUN_ID = Date.now().toString(36).slice(-6);
const YEAR_LABEL = `2025-${RUN_ID}`;
const NEXT_YEAR_LABEL = `2026-${RUN_ID}`;

let yearId: number;
let nextYearId: number;

// ── Suite sérialisée ───────────────────────────────────────────────────────

test.describe.serial("Cycle de vie complet d'une année universitaire", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/admin/academic-years");
    await page.waitForLoadState("networkidle");
    // La table est paginée (25/page par défaut) et n'a pas de recherche : sur une
    // base de test qui accumule des années au fil des runs précédents, l'année
    // créée par ce test peut se retrouver sur une autre page que la première,
    // rendant yearRow() introuvable. Passer à 100/page couvre tous les cas
    // observés (35 années au moment de l'écriture de ce correctif).
    await page.getByRole("combobox").selectOption("100");
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 1. CRÉATION
  // ══════════════════════════════════════════════════════════════════════════

  test("01 — Créer une année universitaire via le formulaire", async ({ page }) => {
    // Ouvrir le modal
    await page.getByRole("button", { name: "Ajouter une année" }).click();
    await expect(page.getByText("Ajouter une annee universitaire")).toBeVisible();

    // Remplir le formulaire (champs name=... du composant AcademicYearForm)
    await page.locator('[name="label"]').fill(YEAR_LABEL);
    await page.locator('[name="start_date"]').fill("2025-09-01");
    await page.locator('[name="end_date"]').fill("2026-08-31");
    await page.locator('[name="wishes_open_date"]').fill("2025-10-01");
    await page.locator('[name="wishes_close_date"]').fill("2025-12-15");

    // Soumettre
    await page.getByRole("button", { name: "Enregistrer", exact: true }).click();

    // Modal fermé, ligne apparaît dans la table
    await expect(page.getByText("Ajouter une annee universitaire")).not.toBeVisible({ timeout: 5_000 });
    await expect(page.getByText(YEAR_LABEL)).toBeVisible({ timeout: 10_000 });

    // Récupérer l'ID via API pour les étapes suivantes
    const token = await getAuthToken(page);
    const resp = await page.request.get(`${API_BASE}/academic/years/?page_size=100`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await resp.json();
    const years: Array<{ id: number; label: string }> = data.results ?? data;
    const created = years.find((y) => y.label === YEAR_LABEL);
    expect(created, `Année ${YEAR_LABEL} non trouvée via API`).toBeDefined();
    yearId = created!.id;
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 2. ÉTAT : INITIALIZATION
  // ══════════════════════════════════════════════════════════════════════════

  test("02 — État Initialisation : badge, boutons et règles d'activation", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    // Badge de statut
    await expect(row.getByText("Initialisation").first()).toBeVisible();

    // Bouton de transition actif
    const transitionBtn = row.getByRole("button", { name: "Ouvrir recommandations", exact: true });
    await expect(transitionBtn).toBeVisible();
    await expect(transitionBtn).toBeEnabled();

    // Modifier actif en Initialisation
    const editBtn = row.getByTitle("Modifier");
    await expect(editBtn).toBeEnabled();

    // Supprimer actif en Initialisation
    const deleteBtn = row.getByTitle("Supprimer");
    await expect(deleteBtn).toBeEnabled();

    // Pas de spinner
    await expect(row.getByText("Calcul en cours…")).not.toBeVisible();

    // Pas de bouton Récupérer
    await expect(row.getByRole("button", { name: "Récupérer", exact: true })).not.toBeVisible();

    // Pas de tiret (réservé à l'état Clôturée)
    await expect(row.locator("text=—").first()).not.toBeVisible();
  });

  test("02b — Initialisation : annuler la modification ne change pas l'état", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);
    await row.getByTitle("Modifier").click();
    await expect(page.getByText(/modifier/i)).toBeVisible();
    await page.getByRole("button", { name: "Annuler", exact: true }).first().click();
    await expect(page.getByText("Ajouter une annee universitaire")).not.toBeVisible();
    await expect(row.getByText("Initialisation").first()).toBeVisible();
  });

  test("02c — Initialisation : annuler la suppression ne supprime pas la ligne", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);
    await row.getByTitle("Supprimer").click();
    // Dialogue de confirmation de suppression
    await expect(page.getByText(/Supprimer l/i)).toBeVisible({ timeout: 5_000 });
    await cancelConfirmDialog(page);
    // L'année est toujours présente (scopé à la ligne : le libellé apparaît
    // aussi dans une carte de stats au-dessus de la table → strict mode
    // violation sur un getByText(YEAR_LABEL) non scopé).
    await expect(row.getByText(YEAR_LABEL)).toBeVisible();
  });

  test("02d — Initialisation : annuler la transition ne change pas le statut", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);
    await row.getByRole("button", { name: "Ouvrir recommandations", exact: true }).click();
    await expect(page.getByText("Confirmer : Ouvrir recommandations")).toBeVisible();
    await cancelConfirmDialog(page);
    await expect(row.getByText("Initialisation").first()).toBeVisible();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 3. TRANSITION : initialization → recommendation
  // ══════════════════════════════════════════════════════════════════════════

  test("03 — Transition Initialisation → Recommandation (avec confirmation)", async ({ page }) => {
    // Préconditions métier de open-recommendation : au moins une inscription
    // avec GPA + un accord actif avec quota de département.
    await seedGpaAndQuotas(page, yearId);

    const row = yearRow(page, YEAR_LABEL);

    // Cliquer le bouton
    await row.getByRole("button", { name: "Ouvrir recommandations", exact: true }).click();

    // Vérifier le contenu du dialogue
    await expect(page.getByText("Confirmer : Ouvrir recommandations")).toBeVisible();
    await expect(page.getByText(/toutes les données sont prêtes/i)).toBeVisible();

    // Confirmer
    await confirmAction(page, "Ouvrir recommandations");

    // Attendre le nouveau statut
    await waitForStatusInRow(page, YEAR_LABEL, "Recommandation", 15_000);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 4. ÉTAT : RECOMMENDATION
  // ══════════════════════════════════════════════════════════════════════════

  test("04 — État Recommandation : badge, boutons et règles d'activation", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await expect(row.getByText("Recommandation").first()).toBeVisible();

    // Prochain bouton
    await expect(row.getByRole("button", { name: "Démarrer candidature", exact: true })).toBeEnabled();

    // Modifier encore actif en Recommandation
    await expect(row.getByTitle("Modifier")).toBeEnabled();

    // Supprimer désactivé (uniquement Initialisation autorise la suppression)
    await expect(
      row.getByTitle("Suppression non autorisée — seules les années en phase Initialisation peuvent être supprimées"),
    ).toBeDisabled();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 5. TRANSITION : recommendation → candidature
  // ══════════════════════════════════════════════════════════════════════════

  test("05 — Transition Recommandation → Candidature", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);
    await row.getByRole("button", { name: "Démarrer candidature", exact: true }).click();
    await expect(page.getByText("Confirmer : Démarrer candidature")).toBeVisible();
    await expect(page.getByText(/ouverture de la période de candidature/i)).toBeVisible();
    await confirmAction(page, "Démarrer candidature");
    await waitForStatusInRow(page, YEAR_LABEL, "Candidature", 15_000);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 6. ÉTAT : CANDIDATURE
  // ══════════════════════════════════════════════════════════════════════════

  test("06 — État Candidature : badge, boutons et règles d'activation", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await expect(row.getByText("Candidature").first()).toBeVisible();
    await expect(row.getByRole("button", { name: "Clôturer les vœux", exact: true })).toBeEnabled();

    // Modifier désactivé à partir de Candidature
    await expect(
      row.getByTitle("Modification non autorisée — seules les années en phase Initialisation ou Recommandation peuvent être modifiées"),
    ).toBeDisabled();

    // Supprimer toujours désactivé
    await expect(
      row.getByTitle("Suppression non autorisée — seules les années en phase Initialisation peuvent être supprimées"),
    ).toBeDisabled();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 7. TRANSITION : candidature → import
  // ══════════════════════════════════════════════════════════════════════════

  test("07 — Transition Candidature → Import", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);
    await row.getByRole("button", { name: "Clôturer les vœux", exact: true }).click();
    await expect(page.getByText("Confirmer : Clôturer les vœux")).toBeVisible();
    await expect(page.getByText(/clôture des vœux/i)).toBeVisible();
    await confirmAction(page, "Clôturer les vœux");
    await waitForStatusInRow(page, YEAR_LABEL, "Import", 15_000);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 8. ÉTAT : IMPORT
  // ══════════════════════════════════════════════════════════════════════════

  test("08 — État Import : badge, bouton Lancer l'affectation actif", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await expect(row.getByText("Import").first()).toBeVisible();
    await expect(row.getByRole("button", { name: "Lancer l'affectation", exact: true })).toBeEnabled();

    // Les deux boutons d'action sont désactivés en Import
    await expect(
      row.getByTitle("Modification non autorisée — seules les années en phase Initialisation ou Recommandation peuvent être modifiées"),
    ).toBeDisabled();
    await expect(
      row.getByTitle("Suppression non autorisée — seules les années en phase Initialisation peuvent être supprimées"),
    ).toBeDisabled();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 9. TRANSITION : import → pre_assignment (lancement Gale-Shapley)
  // ══════════════════════════════════════════════════════════════════════════

  test("09 — Transition Import → Affectation (lancement Gale-Shapley)", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await row.getByRole("button", { name: "Lancer l'affectation", exact: true }).click();
    await expect(page.getByText("Confirmer : Lancer l'affectation")).toBeVisible();
    await expect(page.getByText(/tous les vœux ont été importés/i)).toBeVisible();
    await confirmAction(page, "Lancer l'affectation");

    // Après le lancement, le statut passe en pre_assignment OU directement en validation
    // (selon si Celery est en mode eager ou asynchrone)
    await page.waitForFunction(
      (label) => {
        const allRows = document.querySelectorAll("tr");
        for (const r of allRows) {
          if (r.textContent?.includes(label)) {
            return (
              r.textContent.includes("Affectation en cours") ||
              r.textContent.includes("Validation")
            );
          }
        }
        return false;
      },
      YEAR_LABEL,
      { timeout: 30_000 },
    );
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 10. ÉTAT : PRE_ASSIGNMENT (si Celery asynchrone)
  // ══════════════════════════════════════════════════════════════════════════

  test("10 — État pre_assignment : spinner + bouton Récupérer visibles", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    // Ce test est pertinent uniquement si on est encore en pre_assignment
    const inPreAssignment = await row.getByText("Affectation en cours").isVisible().catch(() => false);
    if (!inPreAssignment) {
      // La transition automatique a déjà eu lieu (Celery eager mode) — pas d'erreur
      test.info().annotations.push({ type: "skip-reason", description: "Celery eager : déjà en Validation" });
      return;
    }

    // Badge spécial avec spinner
    await expect(row.getByText("Affectation en cours")).toBeVisible();

    // Texte "Calcul en cours…" dans la colonne Transition
    await expect(row.getByText("Calcul en cours…")).toBeVisible();

    // Bouton "Récupérer" (amber) présent et actif
    const recupererBtn = row.getByRole("button", { name: "Récupérer", exact: true });
    await expect(recupererBtn).toBeVisible();
    await expect(recupererBtn).toBeEnabled();
    await expect(recupererBtn).toHaveAttribute(
      "title",
      /Forcer la transition vers Validation/,
    );

    // Pas de bouton de transition "normal"
    await expect(row.getByRole("button", { name: "Publier les résultats" })).not.toBeVisible();

    // Les deux boutons d'action sont désactivés
    await expect(
      row.getByTitle("Modification non autorisée — seules les années en phase Initialisation ou Recommandation peuvent être modifiées"),
    ).toBeDisabled();
    await expect(
      row.getByTitle("Suppression non autorisée — seules les années en phase Initialisation peuvent être supprimées"),
    ).toBeDisabled();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 11. TRANSITION : pre_assignment → validation (auto ou manuelle via Récupérer)
  // ══════════════════════════════════════════════════════════════════════════

  test("11 — Transition pre_assignment → Validation (auto ou via Récupérer)", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    // Si déjà en Validation, rien à faire
    const alreadyValidation = await row.getByText("Validation").isVisible().catch(() => false);
    if (alreadyValidation) return;

    // Attendre la transition automatique (30 s)
    const autoTransitioned = await row
      .getByText("Validation")
      .waitFor({ timeout: 30_000 })
      .then(() => true)
      .catch(() => false);

    if (!autoTransitioned) {
      // Utiliser le bouton "Récupérer" (transition manuelle de secours)
      const recupererBtn = row.getByRole("button", { name: "Récupérer", exact: true });
      await expect(recupererBtn).toBeVisible({ timeout: 5_000 });
      await recupererBtn.click();

      // Dialogue de confirmation spécifique
      await expect(page.getByText("Confirmer : Récupérer la transition")).toBeVisible();
      await expect(page.getByText(/Forcer la transition/i)).toBeVisible();
      await confirmAction(page, "Récupérer la transition");
    }

    await waitForStatusInRow(page, YEAR_LABEL, "Validation", 15_000);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 12. ÉTAT : VALIDATION
  // ══════════════════════════════════════════════════════════════════════════

  test("12 — État Validation : badge, bouton Publier actif, pas de spinner", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await expect(row.getByText("Validation").first()).toBeVisible();
    await expect(row.getByRole("button", { name: "Publier les résultats", exact: true })).toBeEnabled();

    // Plus de spinner ni de Récupérer
    await expect(row.getByText("Calcul en cours…")).not.toBeVisible();
    await expect(row.getByRole("button", { name: "Récupérer", exact: true })).not.toBeVisible();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 13. TRANSITION : validation → published
  // ══════════════════════════════════════════════════════════════════════════

  test("13 — Transition Validation → Publiée", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);
    await row.getByRole("button", { name: "Publier les résultats", exact: true }).click();
    await expect(page.getByText("Confirmer : Publier les résultats")).toBeVisible();
    await expect(page.getByText(/toutes les corrections sont validées/i)).toBeVisible();
    await confirmAction(page, "Publier les résultats");
    await waitForStatusInRow(page, YEAR_LABEL, "Publiée", 15_000);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 14. ÉTAT : PUBLISHED
  // ══════════════════════════════════════════════════════════════════════════

  test("14 — État Publiée : badge, bouton Finaliser CTI actif", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await expect(row.getByText("Publiée").first()).toBeVisible();
    await expect(
      row.getByRole("button", { name: "Finaliser les statistiques CTI", exact: true }),
    ).toBeEnabled();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 15. TRANSITION : published → finalization
  // ══════════════════════════════════════════════════════════════════════════

  test("15 — Transition Publiée → Finalisation CTI", async ({ page }) => {
    await performTransition(
      page,
      YEAR_LABEL,
      "Finaliser les statistiques CTI",
      "Finalisation CTI",
      20_000,
    );
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 16. ÉTAT : FINALIZATION
  // ══════════════════════════════════════════════════════════════════════════

  test("16 — État Finalisation CTI : badge, bouton Clôturer actif", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await expect(row.getByText("Finalisation CTI").first()).toBeVisible();
    await expect(row.getByRole("button", { name: "Clôturer l'année", exact: true })).toBeEnabled();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 17. TRANSITION : finalization → closed (IRRÉVERSIBLE)
  // ══════════════════════════════════════════════════════════════════════════

  test("17 — Transition Finalisation → Clôturée (message irréversible + confirmation)", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await row.getByRole("button", { name: "Clôturer l'année", exact: true }).click();

    // Le message de confirmation doit mentionner "irréversible"
    await expect(page.getByText(/irréversible/i)).toBeVisible();
    await expect(page.getByText("Confirmer : Clôturer l'année")).toBeVisible();

    await confirmAction(page, "Clôturer l'année");
    await waitForStatusInRow(page, YEAR_LABEL, "Clôturée", 15_000);
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 18. ÉTAT : CLOSED
  // ══════════════════════════════════════════════════════════════════════════

  test("18 — État Clôturée : tiret, tous boutons désactivés, plus de transition", async ({ page }) => {
    const row = yearRow(page, YEAR_LABEL);

    await expect(row.getByText("Clôturée").first()).toBeVisible();

    // Colonne Transition affiche un tiret "—"
    await expect(row.locator("span").filter({ hasText: "—" }).first()).toBeVisible();

    // Pas de bouton de transition
    await expect(row.getByRole("button", { name: "Clôturer l'année" })).not.toBeVisible();

    // Modifier désactivé
    await expect(
      row.getByTitle("Modification non autorisée — seules les années en phase Initialisation ou Recommandation peuvent être modifiées"),
    ).toBeDisabled();

    // Supprimer désactivé
    await expect(
      row.getByTitle("Suppression non autorisée — seules les années en phase Initialisation peuvent être supprimées"),
    ).toBeDisabled();
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 19. INITIALISATION DE L'ANNÉE SUIVANTE
  // ══════════════════════════════════════════════════════════════════════════

  test("19 — Initialiser une nouvelle année après clôture de la précédente", async ({ page }) => {
    // Ouvrir le formulaire
    await page.getByRole("button", { name: "Ajouter une année" }).click();
    await expect(page.getByText("Ajouter une annee universitaire")).toBeVisible();

    // Remplir
    await page.locator('[name="label"]').fill(NEXT_YEAR_LABEL);
    await page.locator('[name="start_date"]').fill("2026-09-01");
    await page.locator('[name="end_date"]').fill("2027-08-31");
    await page.locator('[name="wishes_open_date"]').fill("2026-10-01");
    await page.locator('[name="wishes_close_date"]').fill("2026-12-15");
    await page.getByRole("button", { name: "Enregistrer", exact: true }).click();

    // Nouvelle année en Initialisation
    const newRow = yearRow(page, NEXT_YEAR_LABEL);
    await expect(newRow.getByText("Initialisation").first()).toBeVisible({ timeout: 10_000 });

    // L'ancienne année est toujours Clôturée
    const oldRow = yearRow(page, YEAR_LABEL);
    await expect(oldRow.getByText("Clôturée").first()).toBeVisible();

    // Récupérer l'ID de la nouvelle année pour nettoyage
    const token = await getAuthToken(page);
    const resp = await page.request.get(`${API_BASE}/academic/years/?page_size=100`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await resp.json();
    const years: Array<{ id: number; label: string }> = data.results ?? data;
    const next = years.find((y) => y.label === NEXT_YEAR_LABEL);
    if (next) nextYearId = next.id;
  });

  // ══════════════════════════════════════════════════════════════════════════
  // 20. NETTOYAGE — supprimer la nouvelle année (en Initialisation)
  // ══════════════════════════════════════════════════════════════════════════

  test("20 — Nettoyage : supprimer la nouvelle année de test", async ({ page }) => {
    test.skip(!nextYearId, "Pas créée si le test 19 a échoué"); // NOSONAR (S1607) — raison déjà fournie ci-dessus

    // La création de l'année a auto-généré un stub AgreementYear pour chaque
    // accord existant (initialize_new_year_mobility) ; il faut les supprimer
    // avant de pouvoir supprimer l'année (AgreementYear.academic_year = PROTECT).
    await deleteAgreementYearsForLabel(page, NEXT_YEAR_LABEL);

    const newRow = yearRow(page, NEXT_YEAR_LABEL);
    await expect(newRow).toBeVisible({ timeout: 5_000 });

    // Supprimer via le bouton de la table
    await newRow.getByTitle("Supprimer").click();
    await expect(page.getByText(/Supprimer l/i)).toBeVisible();
    // .last() : chaque ligne du tableau a aussi un bouton icône "Supprimer" —
    // le bouton de confirmation de la boîte de dialogue est le dernier du DOM.
    await page.getByRole("button", { name: "Supprimer", exact: true }).last().click();

    // La ligne disparaît
    await expect(page.getByText(NEXT_YEAR_LABEL)).not.toBeVisible({ timeout: 10_000 });
  });
});
