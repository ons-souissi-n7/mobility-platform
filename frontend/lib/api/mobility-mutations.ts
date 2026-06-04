import { browserApi } from "@/lib/api/browser-client";
import type {
  Agreement,
  AgreementYear,
  AgreementYearDepartment,
  MobilityCategory,
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

export function getMoveonMobilityImportErrors() {
  return browserApi<RawImport[]>("/mobility/raw-imports/moveon-errors/", {});
}

export function ignoreMobilityImport(id: number) {
  return browserApi<RawImport>(`/mobility/raw-imports/${id}/ignore/`, { method: "PUT" });
}

export function retryMobilityImport(id: number, payload: MobilityImportRetryPayload) {
  return browserApi<RawImport>(`/mobility/raw-imports/${id}/retry/`, { method: "PUT", body: payload });
}

// ── Import Excel ──────────────────────────────────────────────────────────────

export async function importAgreementsFromExcel(file: File) {
  const publicApiBaseUrl = (
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
  ).replace(/\/$/, "");

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
  const publicApiBaseUrl = (
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
  ).replace(/\/$/, "");
  window.open(`${publicApiBaseUrl}/mobility/excel-template/`, "_blank");
}
