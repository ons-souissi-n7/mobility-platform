import { MobilityWorkspace } from "@/components/mobility/mobility-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getExpiringAgreements, getMobilityData } from "@/lib/api/mobility";

export const dynamic = "force-dynamic";

export default async function MobilityPage() {
  const [
    {
      academicYears,
      mobilityCategories,
      agreementYears,
      agreementYearDepartments,
      agreements,
      allAgreements,
      countries,
      currentYear,
      departments,
      importErrors,
      importErrorsTotalCount,
      mobilityLevels,
      universities,
    },
    expiringAgreements,
  ] = await Promise.all([getMobilityData(), getExpiringAgreements(4)]);

  return (
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
        initialAllAgreements={allAgreements}
        initialAgreementYearDepartments={agreementYearDepartments}
        initialImportErrors={importErrors}
        initialImportErrorsTotalCount={importErrorsTotalCount}
        initialExpiringAgreements={expiringAgreements}
        mobilityLevels={mobilityLevels}
        universities={universities}
      />
    </div>
  );
}
