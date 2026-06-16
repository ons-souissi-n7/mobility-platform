"use client";

import { useState } from "react";
import { BookOpen, Building2, Globe2, GraduationCap, University } from "lucide-react";

import { ReferencesWorkspace } from "@/components/references/references-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import type {
  Country,
  Department,
  Level,
  PagedResponse,
  Parcours,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

type ReferencesContainerProps = {
  initialCountries: Country[];
  initialDepartments: Department[];
  initialUniversities: PagedResponse<PartnerUniversity>;
  initialUniversityImportErrors: RawImport[];
  initialDepartmentImportErrors: RawImport[];
  initialMobilityLevels: Level[];
  initialLevelImportErrors: RawImport[];
  initialParcours: Parcours[];
};

export function ReferencesContainer({
  initialCountries,
  initialDepartments,
  initialUniversities,
  initialUniversityImportErrors,
  initialDepartmentImportErrors,
  initialMobilityLevels,
  initialLevelImportErrors,
  initialParcours,
}: ReferencesContainerProps) {
  const [countries, setCountries] = useState(initialCountries);
  const [departments, setDepartments] = useState(initialDepartments);
  const [universities, setUniversities] = useState<PagedResponse<PartnerUniversity>>(initialUniversities);
  const [universityImportErrors, setUniversityImportErrors] = useState(initialUniversityImportErrors);
  const [departmentImportErrors, setDepartmentImportErrors] = useState(initialDepartmentImportErrors);
  const [mobilityLevels, setMobilityLevels] = useState(initialMobilityLevels);
  const [levelImportErrors, setLevelImportErrors] = useState(initialLevelImportErrors);
  const [parcours, setParcours] = useState(initialParcours);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Referentiels"
        description="Administrez les pays, departements, universites partenaires, niveaux et parcours."
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-5">
        <StatCard
          helper="Departements pedagogiques N7"
          icon={Building2}
          label="Departements"
          tone="emerald"
          value={departments.length}
        />
        <StatCard
          helper="Parcours pedagogiques"
          icon={GraduationCap}
          label="Parcours"
          tone="emerald"
          value={parcours.length}
        />
        <StatCard
          helper="Niveaux d'etude"
          icon={BookOpen}
          label="Niveaux"
          tone="blue"
          value={mobilityLevels.length}
        />
        <StatCard
          helper="Etablissements partenaires"
          icon={University}
          label="Universites partenaires"
          tone="amber"
          value={universities.count}
        />
        <StatCard
          helper="Referentiel international"
          icon={Globe2}
          label="Pays"
          tone="blue"
          value={countries.length}
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
        parcours={parcours}
        setParcours={setParcours}
      />
    </div>
  );
}
