import { getApi } from "@/lib/api/client";
import { getCachedAcademicYears, getCachedCurrentYear } from "@/lib/api/server-cache";
import type { SelectOption } from "@/lib/api/types";

export function getAcademicYearSelectOptions(): Promise<SelectOption[]> {
  return getApi<SelectOption[]>("/academic/years/select-options/");
}

export async function getAcademicYearsData() {
  const [years, currentYear] = await Promise.all([
    getCachedAcademicYears(),
    getCachedCurrentYear(),
  ]);

  return {
    currentYear,
    years,
  };
}
