import { getApi } from "@/lib/api/client";
import type {
  Country,
  Department,
  Level,
  Parcours,
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
    parcours,
  ] = await Promise.all([
    getApi<Country[]>("/reference/countries/"),
    getApi<Department[]>("/reference/departments/"),
    getApi<PartnerUniversity[]>("/institutions/universities/"),
    getApi<RawImport[]>("/institutions/import-errors/"),
    getApi<RawImport[]>("/reference/departments/import-errors/"),
    getApi<Level[]>("/reference/levels/"),
    getApi<RawImport[]>("/reference/levels/import-errors/"),
    getApi<Parcours[]>("/reference/parcours/"),
  ]);

  return {
    countries,
    departments,
    universities,
    universityImportErrors,
    departmentImportErrors,
    mobilityLevels,
    levelImportErrors,
    parcours,
  };
}
