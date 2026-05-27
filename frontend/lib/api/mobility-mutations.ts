import { browserApi } from "@/lib/api/browser-client";
import type {
  Agreement,
  AgreementDepartmentConstraint,
  MobilityCategory,
  AgreementLevelConstraint,
  AgreementQuota,
  AgreementYearAvailability,
  DepartmentQuota,
  RawImport,
} from "@/lib/api/types";

export type AgreementPayload = {
  name: string;
  partner_university_id: number;
  framework_ref_id: number | null;
  is_active: boolean;
  remarks: string;
};

export type AgreementQuotaPayload = {
  agreement_id: number;
  academic_year_label: string;
  academic_year_id: number | null;
  period: string;
  total_places: number;
  remaining_places: number;
  source_total_places: number | null;
  remarks: string;
  source_institutions: string;
};

export type AgreementYearAvailabilityPayload = Omit<
  AgreementYearAvailability,
  "id" | "created_at" | "updated_at"
>;

export type AgreementDepartmentConstraintPayload = Omit<
  AgreementDepartmentConstraint,
  "id" | "created_at" | "updated_at"
>;

export type AgreementLevelConstraintPayload = Omit<
  AgreementLevelConstraint,
  "id" | "created_at" | "updated_at"
>;

export type DepartmentQuotaPayload = Omit<
  DepartmentQuota,
  "id" | "created_at" | "updated_at" | "estimated_places" | "is_validated" | "validated_by" | "validated_at"
>;

export type MobilityImportRetryPayload = {
  partner_university_id?: number;
  agreement_id?: number;
  academic_year_id?: number;
  academic_year_label?: string;
  period?: string;
  total_places?: number;
  remaining_places?: number;
  total_duration?: number;
  duration_unit?: string;
};

export type MobilityEstimationResult = {
  eligible_agreements: number;
  quota_created: number;
  department_quota_created: number;
  skipped_existing_quota: number;
  skipped_no_current_year: number;
};

export function createAgreement(payload: AgreementPayload) {
  return browserApi<Agreement>("/mobility/agreements/", {
    method: "POST",
    body: payload,
  });
}

export function updateAgreement(id: number, payload: AgreementPayload) {
  return browserApi<Agreement>(`/mobility/agreements/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteAgreement(id: number) {
  return browserApi<void>(`/mobility/agreements/${id}/`, {
    method: "DELETE",
  });
}

export function createAgreementQuota(payload: AgreementQuotaPayload) {
  return browserApi<AgreementQuota>("/mobility/agreement-quotas/", {
    method: "POST",
    body: payload,
  });
}

export function updateAgreementQuota(id: number, payload: AgreementQuotaPayload) {
  return browserApi<AgreementQuota>(`/mobility/agreement-quotas/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteAgreementQuota(id: number) {
  return browserApi<void>(`/mobility/agreement-quotas/${id}/`, {
    method: "DELETE",
  });
}

export function createAgreementAvailability(payload: AgreementYearAvailabilityPayload) {
  return browserApi<AgreementYearAvailability>("/mobility/agreement-availabilities/", {
    method: "POST",
    body: payload,
  });
}

export function updateAgreementAvailability(
  id: number,
  payload: AgreementYearAvailabilityPayload,
) {
  return browserApi<AgreementYearAvailability>(`/mobility/agreement-availabilities/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function createDepartmentQuota(payload: DepartmentQuotaPayload) {
  return browserApi<DepartmentQuota>("/mobility/department-quotas/", {
    method: "POST",
    body: payload,
  });
}

export function updateDepartmentQuota(id: number, payload: DepartmentQuotaPayload) {
  return browserApi<DepartmentQuota>(`/mobility/department-quotas/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteDepartmentQuota(id: number) {
  return browserApi<void>(`/mobility/department-quotas/${id}/`, {
    method: "DELETE",
  });
}

export function validateAgreementQuota(id: number, validatedBy = "Administrateur") {
  return browserApi<AgreementQuota>(`/mobility/agreement-quotas/${id}/validate/`, {
    method: "POST",
    body: { validated_by: validatedBy },
  });
}

export function validateDepartmentQuota(id: number, validatedBy = "Administrateur") {
  return browserApi<DepartmentQuota>(`/mobility/department-quotas/${id}/validate/`, {
    method: "POST",
    body: { validated_by: validatedBy },
  });
}

export function getAgreements() {
  return browserApi<Agreement[]>("/mobility/agreements/", {});
}

export function getMobilityCategories() {
  return browserApi<MobilityCategory[]>("/mobility/agreement-frameworks/", {});
}

export function getAgreementQuotas() {
  return browserApi<AgreementQuota[]>("/mobility/agreement-quotas/", {});
}

export function getAgreementAvailabilities() {
  return browserApi<AgreementYearAvailability[]>("/mobility/agreement-availabilities/", {});
}

export function getAgreementDepartmentConstraints() {
  return browserApi<AgreementDepartmentConstraint[]>("/mobility/agreement-departments/", {});
}

export function getAgreementLevelConstraints() {
  return browserApi<AgreementLevelConstraint[]>("/mobility/agreement-levels/", {});
}

export function getDepartmentQuotas() {
  return browserApi<DepartmentQuota[]>("/mobility/department-quotas/", {});
}

export function syncMobilityCategoriesFromMoveon() {
  return browserApi<{ task_id: string; message: string }>(
    "/mobility/agreement-frameworks/sync/",
    {
      method: "POST",
    },
  );
}

export function getMoveonMobilityImportErrors() {
  return browserApi<RawImport[]>("/mobility/raw-imports/moveon-errors/", {});
}

export function ignoreMobilityImport(id: number) {
  return browserApi<RawImport>(`/mobility/raw-imports/${id}/ignore/`, {
    method: "PUT",
  });
}

export function retryMobilityImport(id: number, payload: MobilityImportRetryPayload) {
  return browserApi<RawImport>(`/mobility/raw-imports/${id}/retry/`, {
    method: "PUT",
    body: payload,
  });
}

export function syncMobilityFromMoveon() {
  return browserApi<{ task_id: string; message: string }>("/mobility/sync-moveon/", {
    method: "POST",
  });
}

export type MobilityCategoryPayload = {
  name: string;
  external_id: string;
  relation_types: string;
  is_active: boolean;
};

export function createMobilityCategory(payload: MobilityCategoryPayload) {
  return browserApi<MobilityCategory>("/mobility/agreement-frameworks/", {
    method: "POST",
    body: payload,
  });
}

export function updateMobilityCategory(id: number, payload: MobilityCategoryPayload) {
  return browserApi<MobilityCategory>(`/mobility/agreement-frameworks/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteMobilityCategory(id: number) {
  return browserApi<void>(`/mobility/agreement-frameworks/${id}/`, {
    method: "DELETE",
  });
}

export function redistributeAgreementQuota(id: number) {
  return browserApi<DepartmentQuota[]>(`/mobility/agreement-quotas/${id}/redistribute/`, {
    method: "POST",
  });
}

export function estimateCurrentYearMobilityQuotas() {
  return browserApi<MobilityEstimationResult>("/mobility/estimate-current-year/", {
    method: "POST",
  });
}

export async function importAgreementsFromExcel(file: File) {
  const publicApiBaseUrl =
    (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");

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
  const publicApiBaseUrl =
    (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");
  window.open(`${publicApiBaseUrl}/mobility/excel-template/`, "_blank");
}

export function createAgreementDepartmentConstraint(
  payload: AgreementDepartmentConstraintPayload,
) {
  return browserApi<AgreementDepartmentConstraint>("/mobility/agreement-departments/", {
    method: "POST",
    body: payload,
  });
}

export function deleteAgreementDepartmentConstraint(id: number) {
  return browserApi<void>(`/mobility/agreement-departments/${id}/`, {
    method: "DELETE",
  });
}

export function createAgreementLevelConstraint(payload: AgreementLevelConstraintPayload) {
  return browserApi<AgreementLevelConstraint>("/mobility/agreement-levels/", {
    method: "POST",
    body: payload,
  });
}

export function deleteAgreementLevelConstraint(id: number) {
  return browserApi<void>(`/mobility/agreement-levels/${id}/`, {
    method: "DELETE",
  });
}
