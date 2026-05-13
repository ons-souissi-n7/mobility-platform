import { getApi } from "@/lib/api/client";
import type {
  Country,
  Department,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

export async function getReferenceData() {
  const [countries, departments, universities, universityImportErrors] =
    await Promise.all([
      getApi<Country[]>("/reference/countries/"),
      getApi<Department[]>("/reference/departments/"),
      getApi<PartnerUniversity[]>("/institutions/universities/"),
      getApi<RawImport[]>("/institutions/import-errors/"),
    ]);

  return {
    countries,
    departments,
    universities,
    universityImportErrors,
  };
}
