import { ComplementaryWorkspace } from "@/components/complementary/complementary-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getApi } from "@/lib/api/client";
import {
  getCachedAcademicYears,
  getCachedCurrentYear,
} from "@/lib/api/server-cache";
import type { AcademicYear, ComplementaryMobility, PagedResponse } from "@/lib/api/types";

export const dynamic = "force-dynamic";

const EMPTY_PAGE: PagedResponse<ComplementaryMobility> = {
  count: 0,
  page: 1,
  page_size: 25,
  results: [],
};

export default async function MobilitesComplementairesPage() {
  const [academicYears, currentYear] = await Promise.all([
    getCachedAcademicYears() as Promise<AcademicYear[]>,
    getCachedCurrentYear() as Promise<AcademicYear | null>,
  ]);

  const yearFilter = currentYear ? `&year_id=${currentYear.id}` : "";
  const initialPage = await getApi<PagedResponse<ComplementaryMobility>>(
    `/complementary/?page=1&page_size=25${yearFilter}`,
  ).catch(() => EMPTY_PAGE);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Mobilités complémentaires"
        description="Consultez et traitez les demandes de mobilité complémentaire soumises par les étudiants."
      />
      <ComplementaryWorkspace
        initialMobilities={initialPage.results}
        initialTotalCount={initialPage.count}
        academicYears={academicYears}
        currentYear={currentYear}
      />
    </div>
  );
}
