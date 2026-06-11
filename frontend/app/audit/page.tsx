import { ScrollText } from "lucide-react";

import { AuditLogsWorkspace } from "@/components/audit/audit-logs-workspace";
import { AdminShell } from "@/components/layout/admin-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { getAuditLogs } from "@/lib/api/audit";

export const dynamic = "force-dynamic";

export default async function AuditPage() {
  const logs = await getAuditLogs();

  const totalLogs = logs.length;
  const actors = new Set(logs.map((l) => l.actor_username).filter(Boolean)).size;
  const creations = logs.filter((l) => l.action === "create").length;

  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader
          title="Journal d'audit"
          description="Historique des actions effectuées sur les données de la plateforme."
        />

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <StatCard
            helper="Entrées enregistrées au total"
            icon={ScrollText}
            label="Total événements"
            tone="blue"
            value={totalLogs}
          />
          <StatCard
            helper="Utilisateurs ayant effectué une action"
            icon={ScrollText}
            label="Utilisateurs actifs"
            tone="blue"
            value={actors}
          />
          <StatCard
            helper="Nouvelles entités créées"
            icon={ScrollText}
            label="Créations"
            tone="blue"
            value={creations}
          />
        </div>

        <AuditLogsWorkspace initialLogs={logs} />
      </div>
    </AdminShell>
  );
}
