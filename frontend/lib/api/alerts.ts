import { browserApi } from "@/lib/api/browser-client";
import type { SystemAlert } from "@/lib/api/types";

export async function fetchUnreadAlerts(): Promise<SystemAlert[]> {
  return browserApi<SystemAlert[]>("/alerts/", { method: "GET" });
}

export async function acknowledgeAlert(id: number): Promise<void> {
  return browserApi<void>(`/alerts/${id}/acknowledge/`, { method: "POST" });
}
