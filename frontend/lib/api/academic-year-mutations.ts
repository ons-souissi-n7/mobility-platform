import { browserApi } from "@/lib/api/browser-client";
import type { AcademicYear } from "@/lib/api/types";

export type AcademicYearPayload = Omit<
  AcademicYear,
  "id" | "status" | "closed_at" | "created_at" | "updated_at"
>;

export type AcademicYearTransition =
  | "open-recommendation"
  | "start-candidature"
  | "close-wishes"
  | "launch-assignment"
  | "publish-results"
  | "finalize-cti"
  | "close";

export function createAcademicYear(payload: AcademicYearPayload) {
  return browserApi<AcademicYear>("/academic/years/", {
    method: "POST",
    body: payload,
  });
}

export function updateAcademicYear(id: number, payload: AcademicYearPayload) {
  return browserApi<AcademicYear>(`/academic/years/${id}/`, {
    method: "PUT",
    body: payload,
  });
}

export function deleteAcademicYear(id: number) {
  return browserApi<void>(`/academic/years/${id}/`, {
    method: "DELETE",
  });
}

export function applyAcademicYearTransition(
  id: number,
  transition: AcademicYearTransition,
) {
  return browserApi<AcademicYear>(`/academic/years/${id}/${transition}/`, {
    method: "POST",
  });
}
