import { CalendarClock, CheckCircle2, Clock3 } from "lucide-react";

import { AcademicYearsWorkspace } from "@/components/academic-years/academic-years-workspace";
import { statusLabels } from "@/components/academic-years/status";
import { AdminShell } from "@/components/layout/admin-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { getAcademicYearsData } from "@/lib/api/academic-years";

export const dynamic = "force-dynamic";

export default async function AcademicYearsPage() {
  const { currentYear, years } = await getAcademicYearsData();

  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader
          title="Annees universitaires"
          description="Pilotez le cycle de vie de la campagne via une machine a etats securisee."
        />

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <StatCard
            helper="Campagnes configurees"
            icon={CalendarClock}
            label="Annees"
            tone="blue"
            value={years.length}
          />
          <StatCard
            helper={currentYear ? statusLabels[currentYear.status] : "Aucune active"}
            icon={Clock3}
            label="Annee courante"
            tone="emerald"
            value={currentYear?.label ?? "-"}
          />
          <StatCard
            helper="Campagnes archivees ou terminees"
            icon={CheckCircle2}
            label="Cloturees"
            tone="amber"
            value={years.filter((year) => year.status === "closed").length}
          />
        </div>

        <AcademicYearsWorkspace years={years} />
      </div>
    </AdminShell>
  );
}
