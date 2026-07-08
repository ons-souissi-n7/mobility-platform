import { browserApi, browserApiUpload } from "@/lib/api/browser-client";
import { downloadBlob, publicApiBaseUrl } from "@/lib/api/download-utils";
import type {
  PagedResponse,
  RawImport,
  SelectOption,
  StudentStats,
  StudentWithEnrollment,
} from "@/lib/api/types";

type TaskResponse = { task_id: string; message: string };

export async function importStudentsFromExcel(
  yearId: number,
  file: File,
): Promise<TaskResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return browserApiUpload<TaskResponse>(
    `/students/students/import-excel/${yearId}/`,
    formData,
  );
}

export function syncStudentsFromPegase(yearId: number): Promise<TaskResponse> {
  return browserApi<TaskResponse>(
    `/students/students/sync-pegase/${yearId}/`,
    { method: "POST" },
  );
}

export function getStudentStatsForYear(yearId: number): Promise<StudentStats> {
  return browserApi<StudentStats>(
    `/students/students/stats/?academic_year_id=${yearId}`,
    { method: "GET" },
  );
}

export function getStudentSelectOptions(academicYearId?: number): Promise<SelectOption[]> {
  const qs = academicYearId ? `?academic_year_id=${academicYearId}` : "";
  return browserApi<SelectOption[]>(`/students/students/select-options/${qs}`, { method: "GET" });
}

export type StudentByYearFilters = {
  search?: string;
  department_id?: number;
  level_id?: number;
  parcours_id?: number;
  page?: number;
  page_size?: number;
};

export function getStudentsByYear(
  yearId: number,
  filters: StudentByYearFilters = {},
): Promise<PagedResponse<StudentWithEnrollment>> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.department_id) params.set("department_id", String(filters.department_id));
  if (filters.level_id) params.set("level_id", String(filters.level_id));
  if (filters.parcours_id) params.set("parcours_id", String(filters.parcours_id));
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 25));
  return browserApi<PagedResponse<StudentWithEnrollment>>(
    `/students/students/by-year/${yearId}/?${params.toString()}`,
    { method: "GET" },
  );
}

export function getStudentImportErrors(
  params: { page?: number; page_size?: number; year_id?: number } = {},
): Promise<PagedResponse<RawImport>> {
  const qs = new URLSearchParams();
  qs.set("page", String(params.page ?? 1));
  qs.set("page_size", String(params.page_size ?? 25));
  if (params.year_id) qs.set("year_id", String(params.year_id));
  return browserApi<PagedResponse<RawImport>>(
    `/students/students/import-errors/?${qs}`,
    { method: "GET" },
  );
}

export function ignoreStudentImportError(rawImportId: number): Promise<RawImport> {
  return browserApi<RawImport>(
    `/students/students/import-errors/${rawImportId}/ignore/`,
    { method: "PUT" },
  );
}

export type StudentImportCorrection = {
  department_id?: number;
  level_id?: number;
  parcours_id?: number;
  ine?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  gender?: string;
  gpa?: number;
  nationality_iso2?: string;
};

export function retryStudentImportError(
  rawImportId: number,
  correction: StudentImportCorrection,
): Promise<RawImport> {
  return browserApi<RawImport>(
    `/students/students/import-errors/${rawImportId}/retry/`,
    { method: "PUT", body: correction },
  );
}

export async function downloadStudentTemplate(): Promise<void> {
  await downloadBlob(
    `${publicApiBaseUrl}/students/students/template/`,
    "template_etudiants.xlsx",
  );
}

export function getStudentDetail(studentId: number): Promise<import("@/lib/api/types").StudentDetail> {
  return browserApi(`/students/students/${studentId}/`, { method: "GET" });
}

export async function exportStudentsExcel(
  yearId: number,
  filters: { levelId?: string; deptId?: string; parcoursId?: string } = {},
): Promise<void> {
  const params = new URLSearchParams();
  if (filters.levelId) params.set("level_id", filters.levelId);
  if (filters.deptId) params.set("dept_id", filters.deptId);
  if (filters.parcoursId) params.set("parcours_id", filters.parcoursId);
  await downloadBlob(`${publicApiBaseUrl}/students/students/export-excel/${yearId}/?${params}`, "etudiants.xlsx");
}
