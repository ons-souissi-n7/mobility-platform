import { AdminShell } from "@/components/layout/admin-shell";
import { MobilityWorkspace } from "@/components/mobility/mobility-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getMobilityData } from "@/lib/api/mobility";

export const dynamic = "force-dynamic";

export default async function MobilityPage() {
  const {
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
  } = await getMobilityData();

  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader
          title="Mobilite"
          description="Gerez les accords, les quotas et les repartitions par departement."
        />

        <MobilityWorkspace
          academicYears={academicYears}
          agreementAvailabilities={agreementAvailabilities}
          agreementDepartmentConstraints={agreementDepartmentConstraints}
          mobilityCategories={mobilityCategories}
          agreementLevelConstraints={agreementLevelConstraints}
          currentYear={currentYear}
          departments={departments}
          initialAgreementQuotas={agreementQuotas}
          initialAgreements={agreements}
          initialDepartmentQuotas={departmentQuotas}
          initialImportErrors={importErrors}
          mobilityLevels={mobilityLevels}
          universities={universities}
        />
      </div>
    </AdminShell>
  );
}
