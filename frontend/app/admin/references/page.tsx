import { ReferencesContainer } from "@/components/references/references-container";
import { getReferenceData } from "@/lib/api/references";

export const dynamic = "force-dynamic";

export default async function ReferencesPage() {
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
  } = await getReferenceData();

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
    />
  );
}
