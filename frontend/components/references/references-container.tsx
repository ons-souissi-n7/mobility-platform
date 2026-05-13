"use client";

import { useState } from "react";
import { Building2, Download, Globe2, University } from "lucide-react";

import { ReferencesWorkspace } from "@/components/references/references-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import type {
  Country,
  Department,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

type ReferencesContainerProps = {
  initialCountries: Country[];
  initialDepartments: Department[];
  initialUniversities: PartnerUniversity[];
  initialUniversityImportErrors: RawImport[];
  initialDepartmentImportErrors: RawImport[];
};

export function ReferencesContainer({
  initialCountries,
  initialDepartments,
  initialUniversities,
  initialUniversityImportErrors,
  initialDepartmentImportErrors,
}: ReferencesContainerProps) {
  const [countries, setCountries] = useState(initialCountries);
  const [departments, setDepartments] = useState(initialDepartments);
  const [universities, setUniversities] = useState(initialUniversities);
  const [universityImportErrors, setUniversityImportErrors] = useState(
    initialUniversityImportErrors,
  );
  const [departmentImportErrors, setDepartmentImportErrors] = useState(
    initialDepartmentImportErrors,
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Referentiels"
        description="Administrez les pays, departements et universites partenaires utilises par la plateforme."
        actions={
          <>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50"
              type="button"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Exporter
            </button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <StatCard
          helper="Referentiel CTI et international"
          icon={Globe2}
          label="Pays"
          tone="blue"
          value={countries.length}
        />
        <StatCard
          helper="Departements pedagogiques N7"
          icon={Building2}
          label="Departements"
          tone="emerald"
          value={departments.length}
        />
        <StatCard
          helper="Etablissements partenaires"
          icon={University}
          label="Universites partenaires"
          tone="amber"
          value={universities.length}
        />
      </div>

      <ReferencesWorkspace
        countries={countries}
        setCountries={setCountries}
        departments={departments}
        setDepartments={setDepartments}
        universities={universities}
        setUniversities={setUniversities}
        universityImportErrors={universityImportErrors}
        setUniversityImportErrors={setUniversityImportErrors}
        departmentImportErrors={departmentImportErrors}
        setDepartmentImportErrors={setDepartmentImportErrors}
      />
    </div>
  );
}
