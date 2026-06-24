import { getApi } from "@/lib/api/client";
import {
  getCachedAcademicYears,
  getCachedCountries,
  getCachedCurrentYear,
  getCachedDepartments,
  getCachedLevels,
  getCachedMobilityCategories,
} from "@/lib/api/server-cache";
import type {
  Agreement,
  AgreementYear,
  AgreementYearDepartment,
  PagedResponse,
  PartnerUniversity,
  RawImport,
  SelectOption,
} from "@/lib/api/types";

export function getAgreementSelectOptions(): Promise<SelectOption[]> {
  return getApi<SelectOption[]>("/mobility/agreements/select-options/");
}

export function getExpiringAgreements(months = 4): Promise<Agreement[]> {
  return getApi<Agreement[]>(`/mobility/agreements/expiring-soon/?months=${months}`);
}

export type AgreementFilters = {
  search?: string;
  country_id?: number;
  is_active?: boolean;
  page?: number;
  page_size?: number;
};

export function fetchAgreements(filters: AgreementFilters = {}): Promise<PagedResponse<Agreement>> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.country_id) params.set("country_id", String(filters.country_id));
  if (filters.is_active !== undefined) params.set("is_active", String(filters.is_active));
  params.set("page_size", String(filters.page_size ?? 200));
  if (filters.page) params.set("page", String(filters.page));
  return getApi<PagedResponse<Agreement>>(`/mobility/agreements/?${params.toString()}`);
}

export async function getMobilityData() {
  const [
    agreementsPage,
    mobilityCategories,
    agreementYearsPage,
    agreementYearDepartmentsPage,
    importErrors,
    mobilityLevels,
    universitiesPage,
    countries,
    departments,
    academicYears,
    currentYear,
  ] = await Promise.all([
    // Volatile — toujours frais
    getApi<PagedResponse<Agreement>>("/mobility/agreements/?page_size=200"),
    // Stable — mise en cache
    getCachedMobilityCategories(),
    // Volatile
    getApi<PagedResponse<AgreementYear>>("/mobility/agreement-years/?page_size=200"),
    getApi<PagedResponse<AgreementYearDepartment>>("/mobility/agreement-year-departments/?page_size=200"),
    getApi<PagedResponse<RawImport>>("/mobility/raw-imports/moveon-errors/?page=1&page_size=25"),
    // Stable
    getCachedLevels(),
    // Volatile
    getApi<PagedResponse<PartnerUniversity>>("/institutions/universities/?page_size=200"),
    // Stables
    getCachedCountries(),
    getCachedDepartments(),
    getCachedAcademicYears(),
    getCachedCurrentYear(),
  ]);

  return {
    academicYears,
    agreementYears: agreementYearsPage.results,
    agreementYearDepartments: agreementYearDepartmentsPage.results,
    mobilityCategories,
    agreements: agreementsPage.results,
    currentYear,
    countries,
    departments,
    importErrors: importErrors.results,
    importErrorsTotalCount: importErrors.count,
    mobilityLevels,
    universities: universitiesPage.results,
  };
}
