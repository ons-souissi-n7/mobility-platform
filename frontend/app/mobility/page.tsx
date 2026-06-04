import { AdminShell } from "@/components/layout/admin-shell";
import { MobilityWorkspace } from "@/components/mobility/mobility-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getMobilityData } from "@/lib/api/mobility";

export const dynamic = "force-dynamic";

export default async function MobilityPage() {
  const {
    academicYears,
    mobilityCategories,
    agreementYears,
    agreementYearDepartments,
    agreements,
    countries,
    currentYear,
    departments,
    importErrors,
    mobilityLevels,
    universities,
  } = await getMobilityData();

  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader
          title="Mobilité"
          description="Gérez les accords, les quotas annuels et les répartitions par département."
        />

        <MobilityWorkspace
          academicYears={academicYears}
          mobilityCategories={mobilityCategories}
          countries={countries}
          currentYear={currentYear}
          departments={departments}
          initialAgreementYears={agreementYears}
          initialAgreements={agreements}
          initialAgreementYearDepartments={agreementYearDepartments}
          initialImportErrors={importErrors}
          mobilityLevels={mobilityLevels}
          universities={universities}
        />
      </div>
    </AdminShell>
  );
}
