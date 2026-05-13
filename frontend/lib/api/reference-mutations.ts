import { browserApi } from "@/lib/api/browser-client";
import type {
  Country,
  Department,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

export type CountryPayload = Omit<Country, "id">;
export type DepartmentPayload = Omit<Department, "id" | "last_sync_pegase" | "updated_at">;
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

export function getUniversities() {
  return browserApi<PartnerUniversity[]>("/institutions/universities/", {});
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