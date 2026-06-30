import { browserApi } from "@/lib/api/browser-client";
import { downloadBlob, publicApiBaseUrl } from "@/lib/api/download-utils";
import type {
  AgreementYearOption,
  Assignment,
  AssignmentResult,
  AssignmentStats,
  OverrideImportReport,
  PagedResponse,
  RawImport,
  StudentWishes,
} from "@/lib/api/types";

type AssignmentResultFilters = {
  slot_type?: string;
  department_id?: number;
  search?: string;
  page?: number;
  page_size?: number;
};

export function getAssignmentsForYear(
  yearId: number,
): Promise<PagedResponse<Assignment>> {
  return browserApi<PagedResponse<Assignment>>(
    `/outgoing/assignments/?year_id=${yearId}&page_size=20`,
    { method: "GET" },
  );
}

export function getAssignmentResults(
  assignmentId: number,
  filters: AssignmentResultFilters = {},
): Promise<PagedResponse<AssignmentResult>> {
  const params = new URLSearchParams();
  if (filters.slot_type) params.set("slot_type", filters.slot_type);
  if (filters.department_id != null)
    params.set("department_id", String(filters.department_id));
  if (filters.search) params.set("search", filters.search);
  if (filters.page != null) params.set("page", String(filters.page));
  if (filters.page_size != null) params.set("page_size", String(filters.page_size));
  const qs = params.toString() ? `?${params.toString()}` : "";
  return browserApi<PagedResponse<AssignmentResult>>(
    `/outgoing/assignments/${assignmentId}/results/${qs}`,
    { method: "GET" },
  );
}

export function getAssignmentStats(assignmentId: number): Promise<AssignmentStats> {
  return browserApi<AssignmentStats>(
    `/outgoing/assignments/${assignmentId}/stats/`,
    { method: "GET" },
  );
}

export function getAssignmentAgreementYears(
  assignmentId: number,
): Promise<AgreementYearOption[]> {
  return browserApi<AgreementYearOption[]>(
    `/outgoing/assignments/${assignmentId}/agreement-years/`,
    { method: "GET" },
  );
}

// ── Vœux sortants ─────────────────────────────────────────────────────────────

type TaskResponse = { task_id: string; message: string };

export type WishImportCorrection = {
  student_id?: number;
  agreement_id?: number;
};

export function getWishImportErrors(
  params: { page?: number; page_size?: number } = {},
): Promise<PagedResponse<RawImport>> {
  const qs = new URLSearchParams();
  qs.set("page", String(params.page ?? 1));
  qs.set("page_size", String(params.page_size ?? 25));
  return browserApi<PagedResponse<RawImport>>(
    `/outgoing/wishes/import-errors/?${qs}`,
    { method: "GET" },
  );
}

export function retryWishImportError(
  rawImportId: number,
  correction: WishImportCorrection,
): Promise<RawImport> {
  return browserApi<RawImport>(
    `/outgoing/wishes/import-errors/${rawImportId}/retry/`,
    { method: "PUT", body: correction },
  );
}

export async function syncWishesFromMoveon(yearId: number): Promise<TaskResponse> {
  const response = await fetch(
    `${publicApiBaseUrl}/outgoing/wishes/sync-moveon/${yearId}/`,
    { method: "POST" },
  );
  if (!response.ok) throw new Error(`Erreur sync vœux MoveON : ${response.status}`);
  return response.json() as Promise<TaskResponse>;
}

export async function getWishesByYear(yearId: number): Promise<StudentWishes[]> {
  const response = await fetch(
    `${publicApiBaseUrl}/outgoing/wishes/by-year/${yearId}/`,
  );
  if (!response.ok) throw new Error(`Erreur chargement vœux : ${response.status}`);
  return response.json() as Promise<StudentWishes[]>;
}

export async function downloadWishTemplate(yearId: number): Promise<void> {
  const response = await fetch(
    `${publicApiBaseUrl}/outgoing/wishes/template/${yearId}/`,
    { method: "GET" },
  );
  if (!response.ok) throw new Error("Impossible de télécharger le template vœux.");
  const blob = await response.blob();
  const cd = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^"]+)"?/.exec(cd);
  const filename = match?.[1] ?? "template_voeux.xlsx";
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function importWishesFromExcel(
  yearId: number,
  file: File,
): Promise<TaskResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(
    `${publicApiBaseUrl}/outgoing/wishes/import-excel/${yearId}/`,
    { method: "POST", body: formData },
  );
  if (!response.ok) {
    const text = await response.text();
    let message = `Erreur API ${response.status}`;
    try {
      const payload = JSON.parse(text) as { detail?: string };
      if (payload?.detail) message = String(payload.detail);
      else if (text) message = text;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }
  return response.json() as Promise<TaskResponse>;
}

export async function exportWishesExcel(
  yearId: number,
  filters: { deptCode?: string } = {},
): Promise<void> {
  const params = new URLSearchParams();
  if (filters.deptCode) params.set("dept_code", filters.deptCode);
  await downloadBlob(
    `${publicApiBaseUrl}/outgoing/wishes/export-excel/${yearId}/?${params}`,
    "voeux.xlsx",
  );
}

export function validateAssignment(assignmentId: number): Promise<Assignment> {
  return browserApi<Assignment>(
    `/outgoing/assignments/${assignmentId}/validate/`,
    { method: "POST" },
  );
}

export function publishAssignment(assignmentId: number): Promise<Assignment> {
  return browserApi<Assignment>(
    `/outgoing/assignments/${assignmentId}/publish/`,
    { method: "POST" },
  );
}

export type ResultOverridePatch = {
  override_agreement_year_id: number | null;
  override_reason: string;
  force_unassigned?: boolean;
};

export function patchAssignmentResult(
  assignmentId: number,
  resultId: number,
  payload: ResultOverridePatch,
): Promise<AssignmentResult> {
  return browserApi<AssignmentResult>(
    `/outgoing/assignments/${assignmentId}/results/${resultId}/`,
    { method: "PATCH", body: payload },
  );
}

export async function importOverridesFromExcel(
  assignmentId: number,
  file: File,
): Promise<OverrideImportReport> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(
    `${publicApiBaseUrl}/outgoing/assignments/${assignmentId}/import-overrides/`,
    { method: "POST", body: formData },
  );
  if (!response.ok) {
    const text = await response.text();
    let message = `Erreur API ${response.status}`;
    try {
      const payload = JSON.parse(text) as { detail?: string };
      if (payload?.detail) message = String(payload.detail);
      else if (text) message = text;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }
  return response.json() as Promise<OverrideImportReport>;
}
