import { InternshipsWorkspace } from "@/components/internships/internships-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getApi } from "@/lib/api/client";
import {
  getCachedAcademicYears,
  getCachedCountries,
  getCachedCurrentYear,
} from "@/lib/api/server-cache";
import type {
  AcademicYear,
  Country,
  Internship,
  InternshipImportError,
  PagedResponse,
} from "@/lib/api/types";

export const dynamic = "force-dynamic";

export default async function InternshipsPage() {
  const [countries, academicYears, currentYear] = await Promise.all([
    getCachedCountries() as Promise<Country[]>,
    getCachedAcademicYears() as Promise<AcademicYear[]>,
    getCachedCurrentYear() as Promise<AcademicYear | null>,
  ]);

  const yearFilter = currentYear ? `&year_id=${currentYear.id}` : "";
  const [internshipsPage, importErrorsPage] = await Promise.all([
    getApi<PagedResponse<Internship>>(`/internships/?page=1&page_size=25${yearFilter}`),
    getApi<PagedResponse<InternshipImportError>>(
      `/internships/import-errors/?page=1&page_size=25${yearFilter}`,
    ),
  ]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stages internationaux"
        description="Gérez les stages internationaux des étudiants, synchronisez avec Eudonet et traitez les erreurs d'import."
      />

      <InternshipsWorkspace
        initialInternships={internshipsPage.results}
        initialTotalCount={internshipsPage.count}
        countries={countries}
        academicYears={academicYears}
        currentYear={currentYear}
        initialImportErrors={importErrorsPage.results}
        initialImportErrorsTotalCount={importErrorsPage.count}
      />
    </div>
  );
}
