import { browserApi } from "@/lib/api/browser-client";
import type { ComplementaryMobility, PagedResponse } from "./types";

export type ComplementaryAdminFilters = {
  status?: string;
  student_search?: string;
  experience_type?: string;
  year_id?: number;
  page?: number;
  page_size?: number;
};

export async function fetchComplementaryMobilitiesAdmin(
  filters: ComplementaryAdminFilters = {},
): Promise<PagedResponse<ComplementaryMobility>> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.student_search) params.set("student_search", filters.student_search);
  if (filters.experience_type) params.set("experience_type", filters.experience_type);
  if (filters.year_id) params.set("year_id", String(filters.year_id));
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.page_size ?? 25));
  return browserApi<PagedResponse<ComplementaryMobility>>(
    `/complementary/?${params.toString()}`,
    { method: "GET" },
  );
}

export async function validateMobility(id: number): Promise<ComplementaryMobility> {
  return browserApi<ComplementaryMobility>(`/complementary/${id}/validate/`, {
    method: "POST",
  });
}

export async function rejectMobility(
  id: number,
  reason: string,
): Promise<ComplementaryMobility> {
  return browserApi<ComplementaryMobility>(`/complementary/${id}/reject/`, {
    method: "POST",
    body: { reason },
  });
}
