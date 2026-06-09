import { AdminShell } from "@/components/layout/admin-shell";
import { WishesWorkspace } from "@/components/students/wishes-workspace";
import { PageHeader } from "@/components/ui/page-header";
import { getWishesData } from "@/lib/api/students";

export const dynamic = "force-dynamic";

export default async function VoeuxPage() {
  const { academicYears } = await getWishesData();

  return (
    <AdminShell>
      <div className="space-y-6">
        <PageHeader
          title="Vœux étudiants"
          description="Consultez et synchronisez les vœux ordonnés des étudiants depuis MoveON."
        />
        <WishesWorkspace academicYears={academicYears} />
      </div>
    </AdminShell>
  );
}
