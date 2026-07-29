import { CtiExportPanel } from "@/components/cti/cti-export-panel";
import { PageHeader } from "@/components/ui/page-header";
import { getCachedAcademicYears } from "@/lib/api/server-cache";

export const dynamic = "force-dynamic";

export default async function StatistiquesPage() {
  const years = await getCachedAcademicYears();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Statistiques CTI"
        description="Indicateurs et exports requis pour le rapport CTI."
      />
      <CtiExportPanel years={years} />
    </div>
  );
}
