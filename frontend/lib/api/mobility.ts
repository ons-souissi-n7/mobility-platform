import { getApi } from "@/lib/api/client";
import type {
  AcademicYear,
  Agreement,
  AgreementYear,
  AgreementYearDepartment,
  Country,
  Department,
  Level,
  MobilityCategory,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

export async function getMobilityData() {
  const [
    agreements,
    mobilityCategories,
    agreementYears,
    agreementYearDepartments,
    importErrors,
    mobilityLevels,
    universities,
    countries,
    departments,
    academicYears,
    currentYear,
  ] = await Promise.all([
    getApi<Agreement[]>("/mobility/agreements/"),
    getApi<MobilityCategory[]>("/mobility/agreement-categories/"),
    getApi<AgreementYear[]>("/mobility/agreement-years/"),
    getApi<AgreementYearDepartment[]>("/mobility/agreement-year-departments/"),
    getApi<RawImport[]>("/mobility/raw-imports/moveon-errors/"),
    getApi<Level[]>("/reference/levels/"),
    getApi<PartnerUniversity[]>("/institutions/universities/"),
    getApi<Country[]>("/reference/countries/"),
    getApi<Department[]>("/reference/departments/"),
    getApi<AcademicYear[]>("/academic/years/"),
    getApi<AcademicYear | null>("/academic/years/current/"),
  ]);

  return {
    academicYears,
    agreementYears,
    agreementYearDepartments,
    mobilityCategories,
    agreements,
    currentYear,
    countries,
    departments,
    importErrors,
    mobilityLevels,
    universities,
  };
}
