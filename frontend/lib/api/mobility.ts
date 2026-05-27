import { getApi } from "@/lib/api/client";
import type {
  AcademicYear,
  Agreement,
  AgreementDepartmentConstraint,
  MobilityCategory,
  AgreementLevelConstraint,
  AgreementQuota,
  AgreementYearAvailability,
  Department,
  DepartmentQuota,
  Level,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

export async function getMobilityData() {
  const [
    agreements,
    mobilityCategories,
    agreementQuotas,
    agreementAvailabilities,
    agreementDepartmentConstraints,
    departmentQuotas,
    agreementLevelConstraints,
    importErrors,
    mobilityLevels,
    universities,
    departments,
    academicYears,
    currentYear,
  ] = await Promise.all([
    getApi<Agreement[]>("/mobility/agreements/"),
    getApi<MobilityCategory[]>("/mobility/agreement-frameworks/"),
    getApi<AgreementQuota[]>("/mobility/agreement-quotas/"),
    getApi<AgreementYearAvailability[]>("/mobility/agreement-availabilities/"),
    getApi<AgreementDepartmentConstraint[]>("/mobility/agreement-departments/"),
    getApi<DepartmentQuota[]>("/mobility/department-quotas/"),
    getApi<AgreementLevelConstraint[]>("/mobility/agreement-levels/"),
    getApi<RawImport[]>("/mobility/raw-imports/moveon-errors/"),
    getApi<Level[]>("/reference/levels/"),
    getApi<PartnerUniversity[]>("/institutions/universities/"),
    getApi<Department[]>("/reference/departments/"),
    getApi<AcademicYear[]>("/academic/years/"),
    getApi<AcademicYear | null>("/academic/years/current/"),
  ]);

  return {
    academicYears,
    agreementAvailabilities,
    agreementDepartmentConstraints,
    mobilityCategories,
    agreementLevelConstraints,
    agreementQuotas,
    agreements,
    currentYear,
    departments,
    departmentQuotas,
    importErrors,
    mobilityLevels,
    universities,
  };
}
