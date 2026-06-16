import {
  getCachedAcademicYears,
  getCachedDepartments,
  getCachedLevels,
  getCachedParcours,
} from "@/lib/api/server-cache";

export async function getStudentsData() {
  const [academicYears, departments, levels, parcourses] = await Promise.all([
    getCachedAcademicYears(),
    getCachedDepartments(),
    getCachedLevels(),
    getCachedParcours(),
  ]);

  return { academicYears, departments, levels, parcourses };
}

export async function getWishesData() {
  const academicYears = await getCachedAcademicYears();
  return { academicYears };
}
