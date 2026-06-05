import { browserApi } from "@/lib/api/browser-client";
import type {
  ImportReport,
  RawImport,
  StudentStats,
  StudentWithEnrollment,
  StudentWishes,
  WishSyncReport,
} from "@/lib/api/types";

const publicApiBaseUrl = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
).replace(/\/$/, "");

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
