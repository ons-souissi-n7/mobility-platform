import { getApi } from "@/lib/api/client";
import type { AcademicYear } from "@/lib/api/types";

export async function getAcademicYearsData() {
  const [years, currentYear] = await Promise.all([
    getApi<AcademicYear[]>("/academic/years/"),
    getApi<AcademicYear | null>("/academic/years/current/"),
  ]);

  return {
    currentYear,
    years,
  };
}
