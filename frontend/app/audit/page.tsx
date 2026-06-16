import { Eye, FilePlus, PenLine, ScrollText, Trash2 } from "lucide-react";

import { AuditLogsWorkspace } from "@/components/audit/audit-logs-workspace";
import { AdminShell } from "@/components/layout/admin-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { getAuditLogs } from "@/lib/api/audit";

export const dynamic = "force-dynamic";

export default async function AuditPage() {
  const [data, creations, updates, deletions, accesses] = await Promise.all([
    getAuditLogs({ page: 1, page_size: 50 }),
    getAuditLogs({ action: "create", page_size: 1 }),
    getAuditLogs({ action: "update", page_size: 1 }),
    getAuditLogs({ action: "delete", page_size: 1 }),
    getAuditLogs({ action: "access", page_size: 1 }),
  ]);

  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader
          title="Journal d'audit"
          description="Historique des actions effectuées sur les données de la plateforme."
        />

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <StatCard
            helper="Entrées enregistrées au total"
            icon={ScrollText}
            label="Total"
            tone="blue"
            value={data.count}
          />
          <StatCard
            helper="Créations enregistrées"
            icon={FilePlus}
            label="Créations"
            tone="emerald"
            value={creations.count}
          />
          <StatCard
            helper="Modifications enregistrées"
            icon={PenLine}
            label="Modifications"
            tone="blue"
            value={updates.count}
          />
          <StatCard
            helper="Suppressions enregistrées"
            icon={Trash2}
            label="Suppressions"
            tone="amber"
            value={deletions.count}
          />
          <StatCard
            helper="Accès enregistrés"
            icon={Eye}
            label="Accès"
            tone="blue"
            value={accesses.count}
          />
        </div>

        <AuditLogsWorkspace initialData={data} />
      </div>
    </AdminShell>
  );
}
