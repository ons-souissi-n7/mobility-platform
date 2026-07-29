import { OutgoingWorkspace } from "@/components/outgoing/outgoing-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getAffectationsData } from "@/lib/api/outgoing";
import {
  getCachedDepartments,
  getCachedLevels,
  getCachedParcours,
} from "@/lib/api/server-cache";
import type { Department, Level, Parcours } from "@/lib/api/types";

export const dynamic = "force-dynamic";

export default async function SortantesPage() {
  const [{ academicYears }, departments, levels, parcourses] = await Promise.all([
    getAffectationsData(),
    getCachedDepartments() as Promise<Department[]>,
    getCachedLevels() as Promise<Level[]>,
    getCachedParcours() as Promise<Parcours[]>,
  ]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Mobilites sortantes"
        description="Voeux des etudiants et decisions d'affectation Gale-Shapley par annee universitaire."
      />
      <OutgoingWorkspace
        academicYears={academicYears}
        departments={departments}
        levels={levels}
        parcourses={parcourses}
      />
    </div>
  );
}
