import { getApi } from "@/lib/api/client";
import type { Country, Department, PartnerUniversity } from "@/lib/api/types";

export async function getReferenceData() {
  const [countries, departments, universities] = await Promise.all([
    getApi<Country[]>("/reference/countries/"),
    getApi<Department[]>("/reference/departments/"),
    getApi<PartnerUniversity[]>("/institutions/universities/"),
  ]);

  return {
    countries,
    departments,
    universities,
  };
}
