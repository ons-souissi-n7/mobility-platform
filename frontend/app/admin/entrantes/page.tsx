import { IncomingWorkspace } from "@/components/incoming/incoming-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getApi } from "@/lib/api/client";
import {
  getCachedAcademicYears,
  getCachedCountries,
  getCachedCurrentYear,
  getCachedDepartments,
  getCachedLevels,
  getCachedMobilityCategories,
  getCachedParcours,
  getCachedPartnerUniversities,
} from "@/lib/api/server-cache";
import type {
  AcademicYear,
  Country,
  Department,
  IncomingImportError,
  IncomingStudent,
  Level,
  MobilityCategory,
  Parcours,
  PagedResponse,
  SelectOption,
} from "@/lib/api/types";

export const dynamic = "force-dynamic";

const EMPTY_PAGE = <T,>(): PagedResponse<T> => ({
  count: 0,
  page: 1,
  page_size: 25,
  results: [],
});

export default async function EntrantesPage() {
  const [
    countries,
    academicYears,
    currentYear,
    departments,
    levels,
    parcours,
    mobilityCategories,
    universities,
  ] = await Promise.all([
    getCachedCountries() as Promise<Country[]>,
    getCachedAcademicYears() as Promise<AcademicYear[]>,
    getCachedCurrentYear() as Promise<AcademicYear | null>,
    getCachedDepartments() as Promise<Department[]>,
    getCachedLevels() as Promise<Level[]>,
    getCachedParcours() as Promise<Parcours[]>,
    getCachedMobilityCategories() as Promise<MobilityCategory[]>,
    getCachedPartnerUniversities().catch(() => [] as SelectOption[]),
  ]);

  const yearFilter = currentYear ? `&year_id=${currentYear.id}` : "";

  const [studentsPage, importErrorsPage] = await Promise.all([
    getApi<PagedResponse<IncomingStudent>>(
      `/incoming/?page=1&page_size=25${yearFilter}`,
    ).catch(() => EMPTY_PAGE<IncomingStudent>()),
    getApi<PagedResponse<IncomingImportError>>(
      `/incoming/import-errors/?page=1&page_size=25${yearFilter}`,
    ).catch(() => EMPTY_PAGE<IncomingImportError>()),
  ]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Mobilités entrantes"
        description="Gérez les étudiants en mobilité entrante, importez depuis Excel et consultez les statistiques."
      />
      <IncomingWorkspace
        initialStudents={studentsPage.results}
        initialTotalCount={studentsPage.count}
        initialImportErrors={importErrorsPage.results}
        initialImportErrorsCount={importErrorsPage.count}
        academicYears={academicYears}
        currentYear={currentYear}
        countries={countries}
        departments={departments}
        levels={levels}
        parcours={parcours}
        mobilityCategories={mobilityCategories}
        universities={universities}
      />
    </div>
  );
}
