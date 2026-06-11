import { getApi } from "@/lib/api/client";
import type { AcademicYear, ImportReportDetail, ImportReportList } from "@/lib/api/types";

export async function getImportReportsData() {
  const [reports, academicYears] = await Promise.all([
    getApi<ImportReportList[]>("/imports/"),
    getApi<AcademicYear[]>("/academic/years/"),
  ]);
  return { reports, academicYears };
}

export async function getImportReportDetail(id: number): Promise<ImportReportDetail> {
  return getApi<ImportReportDetail>(`/imports/${id}/`);
}
