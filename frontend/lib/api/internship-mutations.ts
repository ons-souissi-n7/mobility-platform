import { browserApi, browserApiUpload } from "@/lib/api/browser-client";
import { downloadBlob, publicApiBaseUrl } from "@/lib/api/download-utils";
import type { ReconciliationCandidate } from "@/lib/api/student-mutations";
import type { Internship, InternshipImportError, PagedResponse } from "@/lib/api/types";

export type { ReconciliationCandidate };

// ── Payload types ──────────────────────────────────────────────────────────────

export type InternshipPayload = {
  student_id: number;
  company_name: string;
  country_id: number | null;
  city: string;
  title: string;
  internship_type: string;
  status_code: string;
  status_label: string;
  start_date: string | null;
  end_date: string | null;
  weeks_in_company: number | null;
  school_tutor: string;
  company_tutor: string;
  academic_year_id: number | null;
};

export type InternshipForcePayload = {
  payload: Partial<{
    ine: string;
    company_name: string;
    start_date: string;
    end_date: string;
    country_name: string;
  }>;
};

// ── CRUD ─────────────────────────────────────────────────────────────────────

export function createInternship(payload: InternshipPayload) {
  return browserApi<Internship>("/internships/", { method: "POST", body: payload });
}

export function updateInternship(id: number, payload: InternshipPayload) {
  return browserApi<Internship>(`/internships/${id}/`, { method: "PUT", body: payload });
}

export function deleteInternship(id: number) {
  return browserApi<void>(`/internships/${id}/`, { method: "DELETE" });
}

// ── Sync Eudonet ──────────────────────────────────────────────────────────────

export function syncInternshipsFromEudonet(yearId?: number) {
  const qs = yearId ? `?year_id=${yearId}` : "";
  return browserApi<{ task_id: string; message: string }>(`/internships/sync/${qs}`, {
    method: "POST",
  });
}

// ── Import Excel ──────────────────────────────────────────────────────────────

export async function importInternshipsFromExcel(yearId: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return browserApiUpload<{ task_id: string; message: string }>(
    `/internships/import/?year_id=${yearId}`,
    formData,
  );
}

// ── Export Excel ──────────────────────────────────────────────────────────────

export async function exportInternshipsExcel(
  yearId?: number,
  countryId?: number,
): Promise<void> {
  const params = new URLSearchParams();
  if (yearId) params.set("year_id", String(yearId));
  if (countryId) params.set("country_id", String(countryId));
  await downloadBlob(
    `${publicApiBaseUrl}/internships/export/?${params.toString()}`,
    "stages.xlsx",
  );
}

export function downloadInternshipTemplate(yearId: number) {
  window.open(`${publicApiBaseUrl}/internships/template/?year_id=${yearId}`, "_blank");
}

// ── Import errors ─────────────────────────────────────────────────────────────

export function getInternshipImportErrors(
  params: { yearId?: number; page?: number; pageSize?: number } = {},
) {
  const qs = new URLSearchParams();
  if (params.yearId) qs.set("year_id", String(params.yearId));
  qs.set("page", String(params.page ?? 1));
  qs.set("page_size", String(params.pageSize ?? 25));
  return browserApi<PagedResponse<InternshipImportError>>(
    `/internships/import-errors/?${qs.toString()}`,
    {},
  );
}

export function retryInternshipImport(id: number) {
  return browserApi<InternshipImportError>(
    `/internships/import-errors/${id}/retry/`,
    { method: "POST" },
  );
}

export function ignoreInternshipImport(id: number) {
  return browserApi<{ status: string }>(
    `/internships/import-errors/${id}/ignore/`,
    { method: "POST" },
  );
}

export function forceInternshipImport(id: number, payload: InternshipForcePayload) {
  return browserApi<InternshipImportError>(
    `/internships/import-errors/${id}/force/`,
    { method: "POST", body: payload },
  );
}

export function addInternshipImportAsNew(id: number) {
  return browserApi<InternshipImportError>(
    `/internships/import-errors/${id}/add/`,
    { method: "POST" },
  );
}

export function getInternshipReconciliationCandidates(
  rawImportId: number,
): Promise<ReconciliationCandidate[]> {
  return browserApi<ReconciliationCandidate[]>(
    `/internships/import-errors/${rawImportId}/candidates/`,
    { method: "GET" },
  );
}
