import { getApi } from "@/lib/api/client";
import type { AuditLog, PagedResponse } from "@/lib/api/types";

export type AuditFilters = {
  entity_type?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
  actor_username?: string;
  page?: number;
  page_size?: number;
};

export async function getAuditLogs(
  filters: AuditFilters = {},
): Promise<PagedResponse<AuditLog>> {
  const params = new URLSearchParams();
  if (filters.entity_type) params.set("entity_type", filters.entity_type);
  if (filters.action) params.set("action", filters.action);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  if (filters.actor_username) params.set("actor_username", filters.actor_username);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.page_size) params.set("page_size", String(filters.page_size));
  const qs = params.toString();
  return getApi<PagedResponse<AuditLog>>("/audit/logs/" + (qs ? `?${qs}` : ""));
}
