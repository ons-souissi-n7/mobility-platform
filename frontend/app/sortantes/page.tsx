import { AdminShell } from "@/components/layout/admin-shell";
import { OutgoingWorkspace } from "@/components/outgoing/outgoing-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getAffectationsData } from "@/lib/api/outgoing";

export const dynamic = "force-dynamic";

export default async function SortantesPage() {
  const { academicYears } = await getAffectationsData();

  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader
          title="Mobilites sortantes"
          description="Voeux des etudiants et decisions d'affectation Gale-Shapley par annee universitaire."
        />
        <OutgoingWorkspace academicYears={academicYears} />
      </div>
    </AdminShell>
  );
}
