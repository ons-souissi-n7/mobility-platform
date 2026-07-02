import { StudentsWorkspace } from "@/components/students/students-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getStudentsData } from "@/lib/api/students";

export const dynamic = "force-dynamic";

export default async function EtudiantsPage() {
  const { academicYears, departments, levels, parcourses } = await getStudentsData();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Etudiants"
        description="Consultez et importez les donnees academiques des etudiants."
      />
      <StudentsWorkspace
        academicYears={academicYears}
        departments={departments}
        levels={levels}
        parcourses={parcourses}
      />
    </div>
  );
}
