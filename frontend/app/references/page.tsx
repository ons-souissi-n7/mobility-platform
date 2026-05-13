import { Building2, Download, Globe2, University } from "lucide-react";

import { ReferencesContainer } from "@/components/references/references-container";
import { AdminShell } from "@/components/layout/admin-shell";
import { getReferenceData } from "@/lib/api/references";

export const dynamic = "force-dynamic";

export default async function ReferencesPage() {
  const {
    countries,
    departments,
    universities,
    universityImportErrors,
    departmentImportErrors,
  } = await getReferenceData();

  return (
    <AdminShell>
      <ReferencesContainer
        initialCountries={countries}
        initialDepartments={departments}
        initialUniversities={universities}
        initialUniversityImportErrors={universityImportErrors}
        initialDepartmentImportErrors={departmentImportErrors}
      />
    </AdminShell>
  );
}
