import {
  getCachedAcademicYears,
  getCachedCountries,
  getCachedDepartments,
  getCachedLevels,
  getCachedParcours,
} from "@/lib/api/server-cache";

export async function getStudentsData() {
  const [academicYears, departments, levels, parcourses, countries] = await Promise.all([
    getCachedAcademicYears(),
    getCachedDepartments(),
    getCachedLevels(),
    getCachedParcours(),
    getCachedCountries(),
  ]);

  return { academicYears, departments, levels, parcourses, countries };
}

export async function getWishesData() {
  const academicYears = await getCachedAcademicYears();
  return { academicYears };
}
