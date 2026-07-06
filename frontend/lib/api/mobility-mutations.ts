import { browserApi } from "@/lib/api/browser-client";
import { downloadBlob, publicApiBaseUrl } from "@/lib/api/download-utils";
import type {
  Agreement,
  AgreementYear,
  AgreementYearDepartment,
  MobilityCategory,
  PagedResponse,
  RawImport,
} from "@/lib/api/types";

// ── Payload types ──────────────────────────────────────────────────────────────

export type AgreementPayload = {
  name: string;
  partner_university_id: number;
  category_id: number | null;
  direction: string;
  valid_from: string | null;
  valid_until: string | null;
  inp_total_places: number;
  inp_institutions: string;
  remarks: string;
  level_ids: number[];
  department_ids: number[];
};

export type AgreementYearPayload = {
  agreement_id: number;
  academic_year_id: number;
  is_active: boolean;
  inp_total_places: number;
  n7_places: number;
};

export type AgreementYearDepartmentPayload = {
  agreement_year_id: number;
  department_id: number;
  estimated_places: number;
};

export type MobilityCategoryPayload = {
  name: string;
};

export type MobilityImportRetryPayload = {
  partner_university_id?: number;
};

export type InitYearResult = {
  eligible_agreements: number;
  year_instances_created: number;
  department_quotas_created: number;
  skipped_existing: number;
};

// ── Accords ───────────────────────────────────────────────────────────────────

export function forceMobilityImport(id: number): Promise<{ status: string; message: string }> {
  return browserApi(`/imports/raw/${id}/force-overwrite/`, { method: "POST" });
}

export async function getAgreements(): Promise<Agreement[]> {
  const page = await browserApi<PagedResponse<Agreement>>(
    "/mobility/agreements/?page_size=500",
    { method: "GET" },
  );
  return page.results;
}

export async function getValidAgreements(): Promise<Agreement[]> {
  const page = await browserApi<PagedResponse<Agreement>>(
    "/mobility/agreements/?valid_only=true&page_size=500",
    { method: "GET" },
  );
  return page.results;
}

export function createAgreement(payload: AgreementPayload) {
  return browserApi<Agreement>("/mobility/agreements/", { method: "POST", body: payload });
}

export function updateAgreement(id: number, payload: AgreementPayload) {
  return browserApi<Agreement>(`/mobility/agreements/${id}/`, { method: "PUT", body: payload });
}

export function deleteAgreement(id: number) {
  return browserApi<void>(`/mobility/agreements/${id}/`, { method: "DELETE" });
}

// ── Instances annuelles ───────────────────────────────────────────────────────

export function createAgreementYear(payload: AgreementYearPayload) {
  return browserApi<AgreementYear>("/mobility/agreement-years/", { method: "POST", body: payload });
}

export function updateAgreementYear(id: number, payload: AgreementYearPayload) {
  return browserApi<AgreementYear>(`/mobility/agreement-years/${id}/`, { method: "PUT", body: payload });
}

export function toggleAgreementYearActive(id: number) {
  return browserApi<AgreementYear>(`/mobility/agreement-years/${id}/toggle-active/`, { method: "POST" });
}

export function validateAgreementYear(id: number, validatedBy = "Administrateur") {
  return browserApi<AgreementYear>(`/mobility/agreement-years/${id}/validate/`, {
    method: "POST",
    body: { validated_by: validatedBy },
  });
}

export function redistributeAgreementYear(id: number) {
  return browserApi<AgreementYearDepartment[]>(`/mobility/agreement-years/${id}/redistribute/`, {
    method: "POST",
  });
}

export function adjustAgreementYearInp(id: number, inpTotalPlaces: number) {
  return browserApi<AgreementYear>(`/mobility/agreement-years/${id}/adjust-inp/`, {
    method: "POST",
    body: { inp_total_places: inpTotalPlaces },
  });
}

export function deleteAgreementYear(id: number) {
  return browserApi<void>(`/mobility/agreement-years/${id}/`, { method: "DELETE" });
}

// ── Quotas départements ───────────────────────────────────────────────────────

export function createAgreementYearDepartment(payload: AgreementYearDepartmentPayload) {
  return browserApi<AgreementYearDepartment>("/mobility/agreement-year-departments/", {
    method: "POST",
    body: payload,
  });
}

export function updateAgreementYearDepartment(id: number, payload: AgreementYearDepartmentPayload) {
  return browserApi<AgreementYearDepartment>(`/mobility/agreement-year-departments/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteAgreementYearDepartment(id: number) {
  return browserApi<void>(`/mobility/agreement-year-departments/${id}/`, { method: "DELETE" });
}

// ── Catégories ────────────────────────────────────────────────────────────────

export function createMobilityCategory(payload: MobilityCategoryPayload) {
  return browserApi<MobilityCategory>("/mobility/agreement-categories/", { method: "POST", body: payload });
}

export function updateMobilityCategory(id: number, payload: MobilityCategoryPayload) {
  return browserApi<MobilityCategory>(`/mobility/agreement-categories/${id}/`, { method: "PUT", body: payload });
}

export function deleteMobilityCategory(id: number) {
  return browserApi<void>(`/mobility/agreement-categories/${id}/`, { method: "DELETE" });
}

export function syncMobilityCategoriesFromMoveon() {
  return browserApi<{ task_id: string; message: string }>("/mobility/agreement-categories/sync/", {
    method: "POST",
  });
}

// ── Sync & init ───────────────────────────────────────────────────────────────

export function syncMobilityFromMoveon() {
  return browserApi<{ task_id: string; message: string }>("/mobility/sync-moveon/", { method: "POST" });
}

export function initializeCurrentYear() {
  return browserApi<InitYearResult>("/mobility/initialize-year/", { method: "POST" });
}

// ── Import erreurs ────────────────────────────────────────────────────────────

export function getMoveonMobilityImportErrors(
  params: { page?: number; page_size?: number } = {},
) {
  const qs = new URLSearchParams();
  qs.set("page", String(params.page ?? 1));
  qs.set("page_size", String(params.page_size ?? 25));
  return browserApi<PagedResponse<RawImport>>(
    `/mobility/raw-imports/moveon-errors/?${qs}`,
    {},
  );
}

export function ignoreMobilityImport(id: number) {
  return browserApi<RawImport>(`/mobility/raw-imports/${id}/ignore/`, { method: "PUT" });
}

export function retryMobilityImport(id: number, payload: MobilityImportRetryPayload) {
  return browserApi<RawImport>(`/mobility/raw-imports/${id}/retry/`, { method: "PUT", body: payload });
}

// ── Import Excel ──────────────────────────────────────────────────────────────

export async function importAgreementsFromExcel(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${publicApiBaseUrl}/mobility/import-excel/`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    let message = `Erreur API ${response.status}`;
    try {
      const payload = JSON.parse(text);
      if (payload?.detail) message = String(payload.detail);
    } catch {
      message = text || message;
    }
    throw new Error(message);
  }
  return response.json() as Promise<{ task_id: string; message: string }>;
}

export function downloadExcelTemplate() {
  window.open(`${publicApiBaseUrl}/mobility/excel-template/`, "_blank");
}

export async function exportAgreementsExcel(filters: {
  yearLabel?: string;
  country?: string;
  category?: string;
  activity?: string;
} = {}): Promise<void> {
  const params = new URLSearchParams();
  if (filters.yearLabel) params.set("year_label", filters.yearLabel);
  if (filters.country && filters.country !== "all") params.set("country", filters.country);
  if (filters.category && filters.category !== "all") params.set("category", filters.category);
  if (filters.activity && filters.activity !== "all") params.set("activity", filters.activity);
  await downloadBlob(`${publicApiBaseUrl}/mobility/agreements/export-excel/?${params}`, "accords.xlsx");
}
