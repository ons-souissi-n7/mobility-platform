import { getApi } from "@/lib/api/client";
import type {
  Country,
  Department,
  Level,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

export async function getReferenceData() {
  const [
    countries,
    departments,
    universities,
    universityImportErrors,
    departmentImportErrors,
    mobilityLevels,
    levelImportErrors,
  ] = await Promise.all([
    getApi<Country[]>("/reference/countries/"),
    getApi<Department[]>("/reference/departments/"),
    getApi<PartnerUniversity[]>("/institutions/universities/"),
    getApi<RawImport[]>("/institutions/import-errors/"),
    getApi<RawImport[]>("/reference/departments/import-errors/"),
    getApi<Level[]>("/reference/levels/"),
    getApi<RawImport[]>("/reference/levels/import-errors/"),
  ]);

  return {
    countries,
    departments,
    universities,
    universityImportErrors,
    departmentImportErrors,
    mobilityLevels,
    levelImportErrors,
  };
}
