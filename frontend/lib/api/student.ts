import { formatApiErrorDetail, publicApiBaseUrl } from "@/lib/api/browser-client";
import type {
  ComplementaryMobility,
  Country,
  StudentAgreement,
  StudentAssignment,
  StudentProfile,
  StudentWishItem,
} from "./types";

function getAuthToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = /(?:^|; )auth_token=([^;]*)/.exec(document.cookie);
  return match ? decodeURIComponent(match[1]) : null;
}

async function throwApiError(res: Response): Promise<never> {
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

async function clientFetch<T>(url: string): Promise<T | null> {
  const token = getAuthToken();
  const res = await fetch(url, {
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (res.status === 404) return null;
  if (!res.ok) await throwApiError(res);
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

export async function fetchComplementaryCountries(): Promise<Country[]> {
  return (
    (await clientFetch<Country[]>(`${publicApiBaseUrl}/complementary/countries/`)) ?? []
  );
}

export async function fetchComplementaryMobilities(
  ine: string,
  yearId?: number,
): Promise<ComplementaryMobility[]> {
  const url = yearId
    ? `${publicApiBaseUrl}/complementary/student/${ine}/?year_id=${yearId}`
    : `${publicApiBaseUrl}/complementary/student/${ine}/`;
  return (await clientFetch<ComplementaryMobility[]>(url)) ?? [];
}

export async function declareComplementaryMobility(
  ine: string,
  fields: {
    academic_year_id: number;
    experience_type: string;
    country_id: number;
    destination_institution: string;
    start_date: string;
    end_date: string;
  },
  document: File,
): Promise<ComplementaryMobility> {
  const params = new URLSearchParams({
    academic_year_id: String(fields.academic_year_id),
    experience_type: fields.experience_type,
    country_id: String(fields.country_id),
    destination_institution: fields.destination_institution,
    start_date: fields.start_date,
    end_date: fields.end_date,
  });
  const form = new FormData();
  form.append("document", document);

  const token = getAuthToken();
  const res = await fetch(
    `${publicApiBaseUrl}/complementary/student/${ine}/?${params.toString()}`,
    {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    },
  );
  if (!res.ok) await throwApiError(res);
  return res.json() as Promise<ComplementaryMobility>;
}
