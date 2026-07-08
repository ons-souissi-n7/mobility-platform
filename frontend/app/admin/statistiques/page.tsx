import { PageHeader } from "@/components/ui/page-header";

export default function StatistiquesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Statistiques CTI"
        description="Indicateurs et exports requis pour le rapport CTI."
      />
      <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-gray-200">
        <p className="text-sm text-gray-400">Statistiques CTI — à développer</p>
      </div>
    </div>
  );
}
