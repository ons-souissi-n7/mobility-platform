import { browserApi, browserApiUpload } from "@/lib/api/browser-client";
import { downloadBlob, publicApiBaseUrl } from "@/lib/api/download-utils";
import type {
  IncomingImportError,
  IncomingStatCountry,
  IncomingStatUniv,
  IncomingStudent,
  PagedResponse,
} from "@/lib/api/types";

type TaskResponse = { task_id: string; message: string };

export type IncomingFilters = {
  year_id?: number;
  country_id?: number;
  department_id?: number;
  level_id?: number;
  parcours_id?: number;
  mobility_category_id?: number;
  university_id?: number;
  search?: string;
  page?: number;
  page_size?: number;
};

export function listIncomingStudents(
  filters: IncomingFilters = {},
): Promise<PagedResponse<IncomingStudent>> {
  const params = new URLSearchParams();
  if (filters.year_id) params.set("year_id", String(filters.year_id));
  if (filters.country_id) params.set("country_id", String(filters.country_id));
  if (filters.department_id) params.set("department_id", String(filters.department_id));
  if (filters.level_id) params.set("level_id", String(filters.level_id));
  if (filters.parcours_id) params.set("parcours_id", String(filters.parcours_id));
  if (filters.mobility_category_id) params.set("mobility_category_id", String(filters.mobility_category_id));
  if (filters.university_id) params.set("university_id", String(filters.university_id));
  if (filters.search) params.set("search", filters.search);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 25));
  return browserApi<PagedResponse<IncomingStudent>>(
    `/incoming/?${params.toString()}`,
    { method: "GET" },
  );
}

export async function importIncomingFromExcel(
  yearId: number,
  file: File,
): Promise<TaskResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return browserApiUpload<TaskResponse>(
    `/incoming/import/?year_id=${yearId}`,
    formData,
  );
}

export async function downloadIncomingTemplate(yearId: number): Promise<void> {
  await downloadBlob(
    `${publicApiBaseUrl}/incoming/template/?year_id=${yearId}`,
    "template_entrants.xlsx",
  );
}

export async function exportIncomingExcel(
  yearId?: number,
  filters: { countryId?: number; departmentId?: number } = {},
): Promise<void> {
  const params = new URLSearchParams();
  if (yearId) params.set("year_id", String(yearId));
  if (filters.countryId) params.set("country_id", String(filters.countryId));
  if (filters.departmentId) params.set("department_id", String(filters.departmentId));
  await downloadBlob(
    `${publicApiBaseUrl}/incoming/export/?${params.toString()}`,
    "entrants.xlsx",
  );
}

export function getIncomingImportErrors(
  params: { year_id?: number; page?: number; page_size?: number } = {},
): Promise<PagedResponse<IncomingImportError>> {
  const qs = new URLSearchParams();
  if (params.year_id) qs.set("year_id", String(params.year_id));
  qs.set("page", String(params.page ?? 1));
  qs.set("page_size", String(params.page_size ?? 25));
  return browserApi<PagedResponse<IncomingImportError>>(
    `/incoming/import-errors/?${qs.toString()}`,
    { method: "GET" },
  );
}

export function ignoreIncomingImportError(rawImportId: number): Promise<IncomingImportError> {
  return browserApi<IncomingImportError>(
    `/incoming/import-errors/${rawImportId}/ignore/`,
    { method: "POST" },
  );
}

export function forceIncomingImportError(
  rawImportId: number,
  payload: Record<string, string>,
): Promise<IncomingImportError> {
  return browserApi<IncomingImportError>(
    `/incoming/import-errors/${rawImportId}/force/`,
    { method: "POST", body: JSON.stringify({ payload }) },
  );
}

export function getIncomingStatsUniv(yearId?: number): Promise<IncomingStatUniv[]> {
  const qs = yearId ? `?year_id=${yearId}` : "";
  return browserApi<IncomingStatUniv[]>(`/incoming/stats/univ/${qs}`, { method: "GET" });
}

export function getIncomingStatsCountry(yearId?: number): Promise<IncomingStatCountry[]> {
  const qs = yearId ? `?year_id=${yearId}` : "";
  return browserApi<IncomingStatCountry[]>(`/incoming/stats/country/${qs}`, { method: "GET" });
}
