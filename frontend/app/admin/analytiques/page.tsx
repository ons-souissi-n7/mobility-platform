import { PageHeader } from "@/components/ui/page-header";
import { AnalyticsDashboard } from "@/components/analytics/analytics-dashboard";

export default function AnalytiquesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Tableaux de bord"
        description="Évolution des flux de mobilité sur les 5 dernières années"
      />
      <AnalyticsDashboard />
    </div>
  );
}
