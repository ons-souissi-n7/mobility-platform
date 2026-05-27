"use client";

import { useState } from "react";
import { BookOpen, Building2, Globe2, University } from "lucide-react";

import { ReferencesWorkspace } from "@/components/references/references-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import type {
  Country,
  Department,
  Level,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

type ReferencesContainerProps = {
  initialCountries: Country[];
  initialDepartments: Department[];
  initialUniversities: PartnerUniversity[];
  initialUniversityImportErrors: RawImport[];
  initialDepartmentImportErrors: RawImport[];
  initialMobilityLevels: Level[];
  initialLevelImportErrors: RawImport[];
};

export function ReferencesContainer({
  initialCountries,
  initialDepartments,
  initialUniversities,
  initialUniversityImportErrors,
  initialDepartmentImportErrors,
  initialMobilityLevels,
  initialLevelImportErrors,
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
  const [mobilityLevels, setMobilityLevels] = useState(initialMobilityLevels);
  const [levelImportErrors, setLevelImportErrors] = useState(initialLevelImportErrors);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Referentiels"
        description="Administrez les pays, departements, universites partenaires et niveaux de mobilite."
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
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
        <StatCard
          helper="Niveaux d'etude"
          icon={BookOpen}
          label="Niveaux"
          tone="blue"
          value={mobilityLevels.length}
        />
      </div>

      <ReferencesWorkspace
        departments={departments}
        setDepartments={setDepartments}
        universities={universities}
        setUniversities={setUniversities}
        universityImportErrors={universityImportErrors}
        setUniversityImportErrors={setUniversityImportErrors}
        departmentImportErrors={departmentImportErrors}
        setDepartmentImportErrors={setDepartmentImportErrors}
        mobilityLevels={mobilityLevels}
        setMobilityLevels={setMobilityLevels}
        levelImportErrors={levelImportErrors}
        setLevelImportErrors={setLevelImportErrors}
        countries={countries}
        setCountries={setCountries}
      />
    </div>
  );
}
