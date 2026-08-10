import { browserApi } from "@/lib/api/browser-client";
import { downloadBlob, publicApiBaseUrl } from "@/lib/api/download-utils";

export interface MobilityTrendPoint {
  label: string;
  outgoing: number;
  incoming: number;
  internships: number;
  complementary: number;
}

export interface MobilityTrendsResponse {
  data: MobilityTrendPoint[];
}

export interface BreakdownSeries {
  label: string;
  values: number[];
}

export interface BreakdownData {
  years: string[];
  series: BreakdownSeries[];
}

export interface BreakdownResponse {
  outgoing: BreakdownData;
  incoming: BreakdownData;
  internships: BreakdownData;
}

export interface SelectOption {
  id: number | string;
  label: string;
}

export function getMobilityTrends(years = 5): Promise<MobilityTrendsResponse> {
  return browserApi<MobilityTrendsResponse>(
    `/analytics/trends/?years=${years}`,
    { method: "GET" }
  );
}

export function getDepartmentBreakdown(
  years = 5,
  deptIds?: number[]
): Promise<BreakdownResponse> {
  const params = new URLSearchParams({ years: String(years) });
  if (deptIds?.length) params.set("dept_ids", deptIds.join(","));
  return browserApi<BreakdownResponse>(`/analytics/by-department/?${params}`, {
    method: "GET",
  });
}

export function getCountryBreakdown(
  years = 5,
  countryIds?: number[]
): Promise<BreakdownResponse> {
  const params = new URLSearchParams({ years: String(years) });
  if (countryIds?.length) params.set("country_ids", countryIds.join(","));
  return browserApi<BreakdownResponse>(`/analytics/by-country/?${params}`, {
    method: "GET",
  });
}

export function getUniversityBreakdown(
  years = 5,
  univIds?: number[]
): Promise<BreakdownResponse> {
  const params = new URLSearchParams({ years: String(years) });
  if (univIds?.length) params.set("univ_ids", univIds.join(","));
  return browserApi<BreakdownResponse>(`/analytics/by-university/?${params}`, {
    method: "GET",
  });
}

export function getDepartmentOptions(): Promise<SelectOption[]> {
  return browserApi<SelectOption[]>("/reference/departments/select-options/", {
    method: "GET",
  });
}

export function getCountryOptions(): Promise<SelectOption[]> {
  return browserApi<SelectOption[]>("/reference/countries/select-options/", {
    method: "GET",
  });
}

export function getUniversityOptions(): Promise<SelectOption[]> {
  return browserApi<SelectOption[]>(
    "/institutions/universities/select-options/",
    { method: "GET" }
  );
}

export function exportAnalytics(years = 5): Promise<void> {
  return downloadBlob(
    `${publicApiBaseUrl}/analytics/export/?years=${years}`,
    `statistiques_mobilite_${years}ans.xlsx`,
  );
}
