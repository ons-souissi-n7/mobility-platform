import { StudentsWorkspace } from "@/components/students/students-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getStudentsData } from "@/lib/api/students";

export const dynamic = "force-dynamic";

export default async function EtudiantsPage() {
  const { academicYears, departments, levels, parcourses, countries } = await getStudentsData();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Étudiants"
        description="Consultez et importez les données académiques des étudiants."
      />
      <StudentsWorkspace
        academicYears={academicYears}
        countries={countries}
        departments={departments}
        levels={levels}
        parcourses={parcourses}
      />
    </div>
  );
}
