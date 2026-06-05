import { getApi } from "@/lib/api/client";
import type { AcademicYear, Department, Level } from "@/lib/api/types";

export async function getStudentsData() {
  const [academicYears, departments, levels] = await Promise.all([
    getApi<AcademicYear[]>("/academic/years/"),
    getApi<Department[]>("/reference/departments/"),
    getApi<Level[]>("/reference/levels/"),
  ]);

  return { academicYears, departments, levels };
}

export async function getWishesData() {
  const academicYears = await getApi<AcademicYear[]>("/academic/years/");
  return { academicYears };
}
