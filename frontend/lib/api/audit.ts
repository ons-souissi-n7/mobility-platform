import { getApi } from "@/lib/api/client";
import type { AuditLog } from "@/lib/api/types";

export type AuditFilters = {
  entity_type?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
  actor_username?: string;
};

export async function getAuditLogs(filters: AuditFilters = {}): Promise<AuditLog[]> {
  const params = new URLSearchParams();
  if (filters.entity_type) params.set("entity_type", filters.entity_type);
  if (filters.action) params.set("action", filters.action);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.actor_username) params.set("actor_username", filters.actor_username);
  const qs = params.toString();
  return getApi<AuditLog[]>(`/audit/logs/${qs ? `?${qs}` : ""}`);
}
