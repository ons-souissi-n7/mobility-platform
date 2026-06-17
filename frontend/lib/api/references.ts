import { getApi } from "@/lib/api/client";
import {
  getCachedCountries,
  getCachedDepartments,
  getCachedLevels,
  getCachedParcours,
} from "@/lib/api/server-cache";
import type {
  PagedResponse,
  PartnerUniversity,
  RawImport,
  SelectOption,
} from "@/lib/api/types";

export function getCountrySelectOptions(): Promise<SelectOption[]> {
  return getApi<SelectOption[]>("/reference/countries/select-options/");
}

export function getDepartmentSelectOptions(): Promise<SelectOption[]> {
  return getApi<SelectOption[]>("/reference/departments/select-options/");
}

export function getLevelSelectOptions(): Promise<SelectOption[]> {
  return getApi<SelectOption[]>("/reference/levels/select-options/");
}

export function getParcoursSelectOptions(departmentId?: number): Promise<SelectOption[]> {
  const qs = departmentId ? `?department_id=${departmentId}` : "";
  return getApi<SelectOption[]>(`/reference/parcours/select-options/${qs}`);
}

export function getUniversitySelectOptions(): Promise<SelectOption[]> {
  return getApi<SelectOption[]>("/institutions/universities/select-options/");
}

export async function getReferenceData() {
  const [
    countries,
    departments,
    universitiesPage,
    universityImportErrors,
    departmentImportErrors,
    mobilityLevels,
    levelImportErrors,
    parcours,
  ] = await Promise.all([
    // Stables — mises en cache
    getCachedCountries(),
    getCachedDepartments(),
    // Volatile — 1re page d'universités (filtrée ensuite côté serveur)
    getApi<PagedResponse<PartnerUniversity>>("/institutions/universities/?page=1&page_size=25"),
    // Volatile — erreurs d'import (1re page)
    getApi<PagedResponse<RawImport>>("/institutions/import-errors/?page=1&page_size=25"),
    getApi<PagedResponse<RawImport>>("/reference/departments/import-errors/?page=1&page_size=25"),
    // Stable
    getCachedLevels(),
    // Volatile
    getApi<PagedResponse<RawImport>>("/reference/levels/import-errors/?page=1&page_size=25"),
    // Stable
    getCachedParcours(),
  ]);

  return {
    countries,
    departments,
    universities: universitiesPage,
    universityImportErrors: universityImportErrors.results,
    universityImportErrorsCount: universityImportErrors.count,
    departmentImportErrors: departmentImportErrors.results,
    departmentImportErrorsCount: departmentImportErrors.count,
    mobilityLevels,
    levelImportErrors: levelImportErrors.results,
    levelImportErrorsCount: levelImportErrors.count,
    parcours,
  };
}
