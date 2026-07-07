import { ReferencesContainer } from "@/components/references/references-container";
import { getCachedCurrentYear } from "@/lib/api/server-cache";
import { getReferenceData } from "@/lib/api/references";

export const dynamic = "force-dynamic";

export default async function ReferencesPage() {
  const [referenceData, currentYear] = await Promise.all([
    getReferenceData(),
    getCachedCurrentYear(),
  ]);

  const {
    countries,
    departments,
    universities,
    universityImportErrors,
    universityImportErrorsCount,
    departmentImportErrors,
    departmentImportErrorsCount,
    mobilityLevels,
    levelImportErrors,
    levelImportErrorsCount,
    parcours,
  } = referenceData;

  return (
    <ReferencesContainer
      initialCountries={countries}
      initialDepartments={departments}
      initialUniversities={universities}
      initialUniversityImportErrors={universityImportErrors}
      initialUniversityImportErrorsCount={universityImportErrorsCount}
      initialDepartmentImportErrors={departmentImportErrors}
      initialDepartmentImportErrorsCount={departmentImportErrorsCount}
      initialMobilityLevels={mobilityLevels}
      initialLevelImportErrors={levelImportErrors}
      initialLevelImportErrorsCount={levelImportErrorsCount}
      initialParcours={parcours}
      currentYear={currentYear}
    />
  );
}
