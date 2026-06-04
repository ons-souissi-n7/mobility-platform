import { browserApi } from "@/lib/api/browser-client";
import type { ImportReport, RawImport, StudentStats, StudentWithEnrollment } from "@/lib/api/types";

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
