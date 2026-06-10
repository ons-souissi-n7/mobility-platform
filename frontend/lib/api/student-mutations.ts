import { browserApi } from "@/lib/api/browser-client";
import { downloadBlob, publicApiBaseUrl } from "@/lib/api/download-utils";
import type {
  ImportReport,
  RawImport,
  StudentStats,
  StudentWithEnrollment,
  StudentWishes,
  WishSyncReport,
} from "@/lib/api/types";

export async function importStudentsFromExcel(
  yearId: number,
  file: File,
): Promise<ImportReport> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${publicApiBaseUrl}/students/students/import-excel/${yearId}/`,
    { method: "POST", body: formData },
  );

  if (!response.ok) {
    const text = await response.text();
    let message = `Erreur API ${response.status}`;
    try {
      const payload = JSON.parse(text);
      if (payload?.detail) message = String(payload.detail);
      else if (text) message = text;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }

  return response.json() as Promise<ImportReport>;
}

export function syncStudentsFromPegase(yearId: number): Promise<ImportReport> {
  return browserApi<ImportReport>(
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

export function getStudentsByYear(yearId: number): Promise<StudentWithEnrollment[]> {
  return browserApi<StudentWithEnrollment[]>(
    `/students/students/by-year/${yearId}/`,
    { method: "GET" },
  );
}

export function getStudentImportErrors(): Promise<RawImport[]> {
  return browserApi<RawImport[]>("/students/students/import-errors/", { method: "GET" });
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

export type WishImportCorrection = {
  student_id?: number;
  agreement_id?: number;
};

export function retryWishImportError(
  rawImportId: number,
  correction: WishImportCorrection,
): Promise<RawImport> {
  return browserApi<RawImport>(
    `/students/students/wishes/import-errors/${rawImportId}/retry/`,
    { method: "PUT", body: correction },
  );
}

export async function downloadStudentTemplate(): Promise<void> {
  const response = await fetch(`${publicApiBaseUrl}/students/students/template/`, {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Impossible de telecharger le template.");
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "template_etudiants.xlsx";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function getStudentDetail(studentId: number): Promise<import("@/lib/api/types").StudentDetail> {
  return browserApi(`/students/students/${studentId}/`, { method: "GET" });
}

export async function syncWishesFromMoveon(yearId: number): Promise<WishSyncReport> {
  const response = await fetch(
    `${publicApiBaseUrl}/students/students/wishes/sync-moveon/${yearId}/`,
    { method: "POST" },
  );
  if (!response.ok) throw new Error(`Erreur sync vœux MoveON : ${response.status}`);
  return response.json() as Promise<WishSyncReport>;
}

export async function getWishesByYear(yearId: number): Promise<StudentWishes[]> {
  const response = await fetch(
    `${publicApiBaseUrl}/students/students/wishes/by-year/${yearId}/`,
  );
  if (!response.ok) throw new Error(`Erreur chargement vœux : ${response.status}`);
  return response.json() as Promise<StudentWishes[]>;
}

export async function downloadWishTemplate(yearId: number): Promise<void> {
  const response = await fetch(
    `${publicApiBaseUrl}/students/students/wishes/template/${yearId}/`,
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
): Promise<WishSyncReport> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(
    `${publicApiBaseUrl}/students/students/wishes/import-excel/${yearId}/`,
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
  return response.json() as Promise<WishSyncReport>;
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

export async function exportWishesExcel(
  yearId: number,
  filters: { deptCode?: string } = {},
): Promise<void> {
  const params = new URLSearchParams();
  if (filters.deptCode) params.set("dept_code", filters.deptCode);
  await downloadBlob(`${publicApiBaseUrl}/students/students/wishes/export-excel/${yearId}/?${params}`, "voeux.xlsx");
}
