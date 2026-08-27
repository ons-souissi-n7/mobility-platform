import { Badge, type BadgeStyle } from "@/components/ui/badge";
import type { ComplementaryMobility } from "@/lib/api/types";

export const MOBILITY_STATUS_MAP: Record<ComplementaryMobility["status"], BadgeStyle> = {
  pending: { label: "En attente", className: "bg-amber-100 text-amber-800" },
  validated: { label: "Validée", className: "bg-green-100 text-green-800" },
  rejected: { label: "Rejetée", className: "bg-red-100 text-red-800" },
};

export function MobilityStatusBadge({ status }: Readonly<{ status: ComplementaryMobility["status"] }>) {
  return <Badge value={status} map={MOBILITY_STATUS_MAP} />;
}
