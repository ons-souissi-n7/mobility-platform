import { formatApiErrorDetail, publicApiBaseUrl } from "@/lib/api/browser-client";
import type {
  StudentAgreement,
  StudentAssignment,
  StudentProfile,
  StudentWishItem,
} from "./types";

async function clientFetch<T>(url: string): Promise<T | null> {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let message = `Erreur API ${res.status}`;
    try {
      const payload = JSON.parse(text);
      if (payload && typeof payload === "object" && "detail" in payload) {
        message = formatApiErrorDetail((payload as { detail: unknown }).detail);
      }
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function fetchStudentProfile(ine: string): Promise<StudentProfile | null> {
  return clientFetch<StudentProfile>(`${publicApiBaseUrl}/student/${ine}/profile/`);
}

export async function fetchStudentAgreements(
  ine: string,
  yearId?: number,
): Promise<StudentAgreement[]> {
  const url = yearId
    ? `${publicApiBaseUrl}/student/${ine}/agreements/?year_id=${yearId}`
    : `${publicApiBaseUrl}/student/${ine}/agreements/`;
  return (await clientFetch<StudentAgreement[]>(url)) ?? [];
}

export async function fetchStudentWishes(
  ine: string,
  yearId?: number,
): Promise<StudentWishItem[]> {
  const url = yearId
    ? `${publicApiBaseUrl}/student/${ine}/wishes/?year_id=${yearId}`
    : `${publicApiBaseUrl}/student/${ine}/wishes/`;
  return (await clientFetch<StudentWishItem[]>(url)) ?? [];
}

export async function fetchStudentAssignment(
  ine: string,
  yearId?: number,
): Promise<StudentAssignment | null> {
  const url = yearId
    ? `${publicApiBaseUrl}/student/${ine}/assignment/?year_id=${yearId}`
    : `${publicApiBaseUrl}/student/${ine}/assignment/`;
  return clientFetch<StudentAssignment>(url);
}
