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

/**
 * Récupère TOUTES les pages d'une ressource paginée. Un `page_size` fixe
 * suffisait tant que le volume restait dessous — ce n'est plus garanti à
 * mesure que les données croissent (ex: quotas département), d'où la boucle
 * plutôt qu'un plafond figé qui tronquerait silencieusement les résultats.
 */
async function fetchAllPages<T>(basePath: string, pageSize = 500): Promise<T[]> {
  const results: T[] = [];
  let page = 1;
  for (;;) {
    const sep = basePath.includes("?") ? "&" : "?";
    const data = await getApi<PagedResponse<T>>(`${basePath}${sep}page=${page}&page_size=${pageSize}`);
    results.push(...data.results);
    if (data.results.length === 0 || results.length >= data.count) break;
    page += 1;
  }
  return results;
}

export async function getMobilityData() {
  const [
    agreements,
    allAgreements,
    mobilityCategories,
    agreementYears,
    agreementYearDepartments,
    importErrors,
    mobilityLevels,
    universities,
    countries,
    departments,
    academicYears,
    currentYear,
  ] = await Promise.all([
    // Volatile — toujours frais
    fetchAllPages<Agreement>("/mobility/agreements/"),
    // Historique complet, y compris les accords supprimés (vue "historique")
    fetchAllPages<Agreement>("/mobility/agreements/?include_deleted=true"),
    // Stable — mise en cache
    getCachedMobilityCategories(),
    // Volatile
    fetchAllPages<AgreementYear>("/mobility/agreement-years/"),
    fetchAllPages<AgreementYearDepartment>("/mobility/agreement-year-departments/"),
    getApi<PagedResponse<RawImport>>("/mobility/raw-imports/moveon-errors/?page=1&page_size=25"),
    // Stable
    getCachedLevels(),
    // Volatile
    fetchAllPages<PartnerUniversity>("/institutions/universities/"),
    // Stables
    getCachedCountries(),
    getCachedDepartments(),
    getCachedAcademicYears(),
    getCachedCurrentYear(),
  ]);

  return {
    academicYears,
    agreementYears,
    agreementYearDepartments,
    mobilityCategories,
    agreements,
    allAgreements,
    currentYear,
    countries,
    departments,
    importErrors: importErrors.results,
    importErrorsTotalCount: importErrors.count,
    mobilityLevels,
    universities,
  };
}
