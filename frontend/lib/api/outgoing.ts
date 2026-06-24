import { getCachedAcademicYears } from "@/lib/api/server-cache";
import type { AcademicYear } from "@/lib/api/types";

export async function getAffectationsData(): Promise<{ academicYears: AcademicYear[] }> {
  const academicYears = await getCachedAcademicYears();
  return { academicYears };
}
