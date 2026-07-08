import { FileBarChart } from "lucide-react";

import { ImportReportsWorkspace } from "@/components/imports/import-reports-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { getImportReportsData } from "@/lib/api/import-reports";

export const dynamic = "force-dynamic";

export default async function RapportsImportPage() {
  const { reports, academicYears } = await getImportReportsData();

  const totalReports = reports.length;
  const totalErrors = reports.reduce((sum, r) => sum + r.error_count, 0);
  const reportsWithErrors = reports.filter((r) => r.error_count > 0).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Rapports d'import"
        description="Consultez l'historique des synchronisations et le detail des erreurs de chaque import."
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <StatCard
          helper="Sessions d'import enregistrees"
          icon={FileBarChart}
          label="Total rapports"
          tone="blue"
          value={totalReports}
        />
        <StatCard
          helper="Rapports avec au moins une erreur"
          icon={FileBarChart}
          label="Avec erreurs"
          tone="amber"
          value={reportsWithErrors}
        />
        <StatCard
          helper="Sur l'ensemble des imports"
          icon={FileBarChart}
          label="Enregistrements rejetés"
          tone="blue"
          value={totalErrors}
        />
      </div>

      <ImportReportsWorkspace reports={reports} academicYears={academicYears} />
    </div>
  );
}
