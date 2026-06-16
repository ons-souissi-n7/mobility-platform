import { browserApi } from "@/lib/api/browser-client";
import type {
  Country,
  Department,
  Level,
  PagedResponse,
  Parcours,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

export type UniversityFilters = {
  search?: string;
  country_id?: number;
  page?: number;
  page_size?: number;
};

export function fetchUniversitiesPage(filters: UniversityFilters = {}): Promise<PagedResponse<PartnerUniversity>> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.country_id) params.set("country_id", String(filters.country_id));
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 25));
  return browserApi<PagedResponse<PartnerUniversity>>(`/institutions/universities/?${params.toString()}`, { method: "GET" });
}

export type CountryPayload = Omit<Country, "id">;
export type DepartmentPayload = Omit<Department, "id" | "last_sync_pegase" | "updated_at">;
export type LevelPayload = Omit<Level, "id" | "created_at" | "updated_at">;
export type ParcoursPayload = Omit<Parcours, "id">;
export type PartnerUniversityPayload = Omit<
  PartnerUniversity,
  "id" | "created_at" | "updated_at"
>;

export function createCountry(payload: CountryPayload) {
  return browserApi<Country>("/reference/countries/", {
    method: "POST",
    body: payload,
  });
}

export function updateCountry(id: number, payload: CountryPayload) {
  return browserApi<Country>(`/reference/countries/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteCountry(id: number) {
  return browserApi<void>(`/reference/countries/${id}/`, {
    method: "DELETE",
  });
}

export function createDepartment(payload: DepartmentPayload) {
  return browserApi<Department>("/reference/departments/", {
    method: "POST",
    body: payload,
  });
}

export function updateDepartment(id: number, payload: DepartmentPayload) {
  return browserApi<Department>(`/reference/departments/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteDepartment(id: number) {
  return browserApi<void>(`/reference/departments/${id}/`, {
    method: "DELETE",
  });
}

export function getDepartments() {
  return browserApi<Department[]>("/reference/departments/", {});
}

export function syncDepartmentsFromPegase() {
  return browserApi<{ task_id: string; message: string }>(
    "/reference/departments/sync-pegase/", 
    {
      method: "POST",
    },
  );
}

export function getDepartmentImportErrors() {
  return browserApi<RawImport[]>("/reference/departments/import-errors/", {});
}


export function retryDepartmentImport(id: number, code: string) {
  return browserApi<RawImport>(`/reference/departments/import-errors/${id}/retry/`, {
    method: "PUT",
    body: { code },
  });
}

export function ignoreDepartmentImport(id: number) {
  return browserApi<RawImport>(`/reference/departments/import-errors/${id}/ignore/`, {
    method: "PUT",
  });
}

export function forceDepartmentImport(id: number) {
  return browserApi<RawImport>(`/reference/departments/import-errors/${id}/force-overwrite/`, {
    method: "POST",
  });
}

export function createUniversity(payload: PartnerUniversityPayload) {
  return browserApi<PartnerUniversity>("/institutions/universities/", {
    method: "POST",
    body: payload,
  });
}

export function updateUniversity(id: number, payload: PartnerUniversityPayload) {
  return browserApi<PartnerUniversity>(`/institutions/universities/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteUniversity(id: number) {
  return browserApi<void>(`/institutions/universities/${id}/`, {
    method: "DELETE",
  });
}

export function syncUniversitiesFromMoveon() {
  return browserApi<{ task_id: string; message: string }>(
    "/institutions/sync-moveon/",
    {
      method: "POST",
    },
  );
}

export function getUniversityImportErrors() {
  return browserApi<RawImport[]>("/institutions/import-errors/", {});
}

export function retryUniversityImport(id: number, countryId: number) {
  return browserApi<RawImport>(`/institutions/import-errors/${id}/retry/`, {
    method: "POST",
    body: { country_id: countryId },
  });
}

export function ignoreUniversityImport(id: number) {
  return browserApi<RawImport>(`/institutions/import-errors/${id}/ignore/`, {
    method: "PUT",
  });
}

export function forceUniversityImport(id: number) {
  return browserApi<RawImport>(`/institutions/import-errors/${id}/force-overwrite/`, {
    method: "POST",
  });
}

export function getLevels() {
  return browserApi<Level[]>("/reference/levels/", {});
}

export function createLevel(payload: LevelPayload) {
  return browserApi<Level>("/reference/levels/", {
    method: "POST",
    body: payload,
  });
}

export function updateLevel(id: number, payload: LevelPayload) {
  return browserApi<Level>(`/reference/levels/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteLevel(id: number) {
  return browserApi<void>(`/reference/levels/${id}/`, {
    method: "DELETE",
  });
}

export function syncLevelsFromPegase() {
  return browserApi<{ task_id: string; message: string }>("/reference/levels/sync/", {
    method: "POST",
  });
}

export function getLevelImportErrors() {
  return browserApi<RawImport[]>("/reference/levels/import-errors/", {});
}

export function ignoreLevelImport(id: number) {
  return browserApi<RawImport>(`/reference/levels/import-errors/${id}/ignore/`, {
    method: "PUT",
  });
}

export function forceLevelImport(id: number) {
  return browserApi<RawImport>(`/reference/levels/import-errors/${id}/force-overwrite/`, {
    method: "POST",
  });
}
export function getParcours(departmentId?: number) {
  const url = departmentId
    ? `/reference/parcours/?department_id=${departmentId}`
    : "/reference/parcours/";
  return browserApi<Parcours[]>(url, {});
}

export function createParcours(payload: ParcoursPayload) {
  return browserApi<Parcours>("/reference/parcours/", {
    method: "POST",
    body: payload,
  });
}

export function updateParcours(id: number, payload: ParcoursPayload) {
  return browserApi<Parcours>(`/reference/parcours/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteParcours(id: number) {
  return browserApi<void>(`/reference/parcours/${id}/`, {
    method: "DELETE",
  });
}
