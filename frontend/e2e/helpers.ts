/**
 * Utilitaires partagés pour les tests E2E.
 *
 * Fournit :
 *  - Accès au token JWT depuis les cookies du navigateur
 *  - Appels API authentifiés (GET / POST / DELETE)
 *  - Helpers de navigation dans la table des années (sélecteur de ligne)
 *  - Helpers FSM : cliquer un bouton de transition, confirmer le dialogue, attendre le statut
 */

import { expect, type Page } from "@playwright/test";

export const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:3000";
export const API_BASE = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";

// ── Auth ───────────────────────────────────────────────────────────────────

/** Lit le JWT depuis le cookie auth_token du contexte navigateur courant. */
export async function getAuthToken(page: Page): Promise<string> {
  const cookies = await page.context().cookies(BASE_URL);
  return cookies.find((c) => c.name === "auth_token")?.value ?? "";
}

// ── Appels API directs (sans passer par l'interface) ──────────────────────

export async function apiGet<T>(page: Page, path: string): Promise<T> {
  const token = await getAuthToken(page);
  const resp = await page.request.get(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok()) {
    throw new Error(`GET ${path} → HTTP ${resp.status()} : ${await resp.text()}`);
  }
  return resp.json() as Promise<T>;
}

export async function apiPost<T>(page: Page, path: string, data: unknown = {}): Promise<T> {
  const token = await getAuthToken(page);
  const resp = await page.request.post(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    data,
  });
  if (!resp.ok()) {
    throw new Error(`POST ${path} → HTTP ${resp.status()} : ${await resp.text()}`);
  }
  const text = await resp.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export async function apiDelete(page: Page, path: string): Promise<void> {
  const token = await getAuthToken(page);
  const resp = await page.request.delete(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok() && resp.status() !== 204) {
    throw new Error(`DELETE ${path} → HTTP ${resp.status()}`);
  }
}

// ── FSM helpers ────────────────────────────────────────────────────────────

/**
 * Renvoie le locator de la ligne `<tr>` contenant le libellé de l'année.
 * Utilise `hasText` pour trouver la première ligne dont le texte contient yearLabel.
 */
export function yearRow(page: Page, yearLabel: string) {
  return page.locator("tr", { hasText: yearLabel }).first();
}

/** Clique sur le bouton de transition dans la ligne de l'année. */
export async function clickTransitionButton(
  page: Page,
  yearLabel: string,
  buttonLabel: string,
): Promise<void> {
  const row = yearRow(page, yearLabel);
  await row.getByRole("button", { name: buttonLabel, exact: true }).click();
}

/**
 * Valide la boîte de dialogue de confirmation (ConfirmDialog).
 * Le bouton "confirmer" a le même texte que l'action passée en paramètre
 * (ex : "Ouvrir recommandations").
 */
export async function confirmAction(page: Page, actionLabel: string): Promise<void> {
  // Le titre du dialogue est "Confirmer : {actionLabel}"
  await expect(page.getByText(`Confirmer : ${actionLabel}`)).toBeVisible({ timeout: 5_000 });
  await page.getByRole("button", { name: actionLabel, exact: true }).last().click();
}

/** Clique "Annuler" dans la boîte de confirmation. */
export async function cancelConfirmDialog(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Annuler", exact: true }).first().click();
}

/**
 * Attend que le badge de statut dans la ligne de l'année affiche `statusLabel`.
 * Timeout configurable (défaut 30 s).
 */
export async function waitForStatusInRow(
  page: Page,
  yearLabel: string,
  statusLabel: string,
  timeout = 30_000,
): Promise<void> {
  const row = yearRow(page, yearLabel);
  await expect(row.locator(".rounded-full, span").filter({ hasText: statusLabel }).first())
    .toBeVisible({ timeout });
}

/**
 * Effectue une transition complète :
 *  1. Clique le bouton de transition
 *  2. Valide le dialogue de confirmation
 *  3. Attend le nouveau statut
 */
export async function performTransition(
  page: Page,
  yearLabel: string,
  buttonLabel: string,
  expectedStatusLabel: string,
  waitTimeout = 20_000,
): Promise<void> {
  await clickTransitionButton(page, yearLabel, buttonLabel);
  await confirmAction(page, buttonLabel);
  await waitForStatusInRow(page, yearLabel, expectedStatusLabel, waitTimeout);
}

// ── Setup de données via API ───────────────────────────────────────────────

export interface AcademicYearData {
  id: number;
  label: string;
  status: string;
}

/**
 * Crée une année universitaire via l'API et la retourne.
 * Utile pour préparer l'état des tests sans passer par l'interface.
 */
export async function createYearViaApi(
  page: Page,
  label: string,
): Promise<AcademicYearData> {
  return apiPost<AcademicYearData>(page, "/academic/years/", {
    label,
    start_date: "2025-09-01",
    end_date: "2026-08-31",
    wishes_open_date: "2025-10-01",
    wishes_close_date: "2025-12-15",
  });
}

/**
 * Avance une année vers un état cible en appelant les endpoints de transition.
 * Transitions disponibles (dans l'ordre) :
 *   initialization → recommendation → candidature → import → validation → published
 */
const TRANSITION_SEQUENCE: Array<{ transition: string; expectedStatus: string }> = [
  { transition: "open-recommendation", expectedStatus: "recommendation" },
  { transition: "start-candidature",   expectedStatus: "candidature" },
  { transition: "close-wishes",        expectedStatus: "import" },
  { transition: "launch-assignment",   expectedStatus: "pre_assignment" },
  { transition: "complete-assignment", expectedStatus: "validation" },
  { transition: "publish-results",     expectedStatus: "published" },
  { transition: "finalize-cti",        expectedStatus: "finalization" },
  { transition: "close",               expectedStatus: "closed" },
];

export async function advanceYearToStatus(
  page: Page,
  yearId: number,
  targetStatus: string,
): Promise<void> {
  let currentStatus = "initialization";

  for (const step of TRANSITION_SEQUENCE) {
    if (currentStatus === targetStatus) break;
    await apiPost(page, `/academic/years/${yearId}/${step.transition}/`, {});
    currentStatus = step.expectedStatus;
    if (currentStatus === targetStatus) break;
  }
}

/** Supprime une année via l'API (ne fonctionne qu'en état initialization). */
export async function deleteYearViaApi(page: Page, yearId: number): Promise<void> {
  await apiDelete(page, `/academic/years/${yearId}/`);
}

// ── Préconditions métier pour open-recommendation ──────────────────────────

/**
 * Seed le minimum requis par les préconditions métier de `open-recommendation` :
 *  - au moins une inscription (AnnualEnrollment) avec un GPA renseigné
 *  - au moins un accord actif avec un quota de département
 *
 * Réutilise les données de référence déjà présentes (départements, universités)
 * et déclenche une synchronisation Pegase (le fixture fake-pegase-api contient
 * des GPA) pour peupler les inscriptions.
 *
 * IMPORTANT : `run_sync_pegase_students` dérive la plage de dates à synchroniser
 * depuis `academic_year.label.split("-")[0]` (converti en int) — le label de
 * l'année ciblée doit donc commencer par une année à 4 chiffres suivie d'un tiret
 * (ex. "2025-xxxxx"), sans quoi la synchronisation échoue silencieusement.
 */
export async function seedGpaAndQuotas(
  page: Page,
  academicYearId: number,
): Promise<{ agreementId: number }> {
  const depts = await apiGet<Array<{ id: number; label: string }>>(
    page,
    "/reference/departments/select-options/",
  );
  const universities = await apiGet<{ results: Array<{ id: number }> }>(
    page,
    "/institutions/universities/?page_size=1",
  );

  const agreement = await apiPost<{ id: number }>(page, "/mobility/agreements/", {
    name: `E2E-AG-${Date.now().toString(36)}`,
    partner_university_id: universities.results[0].id,
    level_ids: [],
  });
  await apiPost(page, "/mobility/agreement-departments/", {
    agreement_id: agreement.id,
    department_id: depts[0].id,
  });
  // is_active + n7_places > 0 déclenche ensure_dept_quotas_on_activation
  // côté backend, qui crée automatiquement les quotas département.
  await apiPost(page, "/mobility/agreement-years/", {
    agreement_id: agreement.id,
    academic_year_id: academicYearId,
    is_active: true,
    n7_places: 5,
    inp_total_places: 5,
  });

  // Le fixture fake-pegase-api contient des GPA (champ "moyenne") pour tous
  // les étudiants — la synchronisation les importe directement.
  await apiPost(page, `/students/students/sync-pegase/${academicYearId}/`, {});
  for (let i = 0; i < 20; i++) {
    const result = await apiGet<{ count: number }>(
      page,
      `/students/students/?academic_year_id=${academicYearId}&page_size=1`,
    );
    if (result.count > 0) return { agreementId: agreement.id };
    await page.waitForTimeout(1_000);
  }
  throw new Error(
    `seedGpaAndQuotas : aucun étudiant importé pour l'année ${academicYearId} après 20s`,
  );
}

/**
 * Supprime toutes les AgreementYear liées à une année (par label). Nécessaire
 * avant de pouvoir supprimer l'année elle-même : `create_academic_year` déclenche
 * automatiquement `initialize_new_year_mobility`, qui crée un stub AgreementYear
 * pour CHAQUE accord existant en base — et `AgreementYear.academic_year` est en
 * `on_delete=PROTECT`, donc la suppression de l'année échoue (409) tant que ces
 * stubs existent, même pour une année fraîchement créée sans aucune donnée propre.
 */
export async function deleteAgreementYearsForLabel(
  page: Page,
  yearLabel: string,
): Promise<void> {
  const result = await apiGet<{ results: Array<{ id: number }> }>(
    page,
    `/mobility/agreement-years/?academic_year=${encodeURIComponent(yearLabel)}&page_size=200`,
  );
  for (const agreementYear of result.results) {
    await apiDelete(page, `/mobility/agreement-years/${agreementYear.id}/`);
  }
}

/** Supprime un accord créé pour les besoins d'un test (best-effort). */
export async function deleteAgreementViaApi(
  page: Page,
  agreementId: number,
): Promise<void> {
  await apiDelete(page, `/mobility/agreements/${agreementId}/`);
}
