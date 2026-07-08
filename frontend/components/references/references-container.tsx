"use client";

import { useState } from "react";
import { BookOpen, Building2, Globe2, GraduationCap, University } from "lucide-react";

import { ReferencesWorkspace } from "@/components/references/references-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import type {
  AcademicYear,
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
  initialUniversityImportErrorsCount: number;
  initialDepartmentImportErrors: RawImport[];
  initialDepartmentImportErrorsCount: number;
  initialMobilityLevels: Level[];
  initialLevelImportErrors: RawImport[];
  initialLevelImportErrorsCount: number;
  initialParcours: Parcours[];
  currentYear: AcademicYear | null;
};

export function ReferencesContainer({
  initialCountries,
  initialDepartments,
  initialUniversities,
  initialUniversityImportErrors,
  initialUniversityImportErrorsCount,
  initialDepartmentImportErrors,
  initialDepartmentImportErrorsCount,
  initialMobilityLevels,
  initialLevelImportErrors,
  initialLevelImportErrorsCount,
  initialParcours,
  currentYear,
}: ReferencesContainerProps) {
  const [countries, setCountries] = useState(initialCountries);
  const [departments, setDepartments] = useState(initialDepartments);
  const [universities, setUniversities] = useState<PagedResponse<PartnerUniversity>>(initialUniversities);
  const [universityImportErrors, setUniversityImportErrors] = useState(initialUniversityImportErrors);
  const [universityImportErrorsCount, setUniversityImportErrorsCount] = useState(initialUniversityImportErrorsCount);
  const [departmentImportErrors, setDepartmentImportErrors] = useState(initialDepartmentImportErrors);
  const [departmentImportErrorsCount, setDepartmentImportErrorsCount] = useState(initialDepartmentImportErrorsCount);
  const [mobilityLevels, setMobilityLevels] = useState(initialMobilityLevels);
  const [levelImportErrors, setLevelImportErrors] = useState(initialLevelImportErrors);
  const [levelImportErrorsCount, setLevelImportErrorsCount] = useState(initialLevelImportErrorsCount);
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
          helper="Établissements partenaires"
          icon={University}
          label="Universités partenaires"
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
        universityImportErrorsCount={universityImportErrorsCount}
        setUniversityImportErrorsCount={setUniversityImportErrorsCount}
        departmentImportErrors={departmentImportErrors}
        setDepartmentImportErrors={setDepartmentImportErrors}
        departmentImportErrorsCount={departmentImportErrorsCount}
        setDepartmentImportErrorsCount={setDepartmentImportErrorsCount}
        mobilityLevels={mobilityLevels}
        setMobilityLevels={setMobilityLevels}
        levelImportErrors={levelImportErrors}
        setLevelImportErrors={setLevelImportErrors}
        levelImportErrorsCount={levelImportErrorsCount}
        setLevelImportErrorsCount={setLevelImportErrorsCount}
        countries={countries}
        setCountries={setCountries}
        parcours={parcours}
        setParcours={setParcours}
        currentYear={currentYear}
      />
    </div>
  );
}
