import { PageHeader } from "@/components/ui/page-header";

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Tableau de bord"
        description="Vue d'ensemble de l'activite de la plateforme."
      />
      <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-gray-200">
        <p className="text-sm text-gray-400">Tableau de bord — à développer</p>
      </div>
    </div>
  );
}
