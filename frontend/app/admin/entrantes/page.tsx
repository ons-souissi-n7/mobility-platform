import { PageHeader } from "@/components/ui/page-header";

export default function EntrantesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Mobilites entrantes"
        description="Gestion des etudiants et partenaires en mobilite entrante."
      />
      <div className="flex h-64 items-center justify-center rounded-lg border-2 border-dashed border-gray-200">
        <p className="text-sm text-gray-400">Mobilites entrantes — à développer</p>
      </div>
    </div>
  );
}
