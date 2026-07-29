import { browserApi } from "@/lib/api/browser-client";
import { downloadBlob, publicApiBaseUrl } from "@/lib/api/download-utils";
import type {
  ComplementaryHistoryItem,
  CtiIncomingRow,
  CtiInternshipRow,
  CtiMobilityRow,
  CtiRegionRow,
  CtiStats,
  ExchangeHistoryItem,
  InternshipHistoryItem,
  MobilityDuration,
  MobilityHistory,
  MobilityTotals,
} from "@/lib/api/types";

export type {
  ComplementaryHistoryItem,
  CtiIncomingRow,
  CtiInternshipRow,
  CtiMobilityRow,
  CtiRegionRow,
  CtiStats,
  ExchangeHistoryItem,
  InternshipHistoryItem,
  MobilityDuration,
  MobilityHistory,
  MobilityTotals,
};

export function getCtiDuration(ine: string): Promise<MobilityDuration> {
  return browserApi<MobilityDuration>(`/cti/students/${ine}/duration/`, { method: "GET" });
}

export function refreshCtiDuration(ine: string): Promise<MobilityDuration> {
  return browserApi<MobilityDuration>(`/cti/students/${ine}/duration/refresh/`, { method: "POST" });
}

export function getCtiHistory(ine: string): Promise<MobilityHistory> {
  return browserApi<MobilityHistory>(`/cti/students/${ine}/history/`, { method: "GET" });
}

export function downloadCtiExport(academicYearId: number): Promise<void> {
  const url = `${publicApiBaseUrl}/cti/export/?academic_year_id=${academicYearId}`;
  return downloadBlob(url, `rapport_cti_${academicYearId}.xlsx`);
}

export function getCtiStats(academicYearId: number): Promise<CtiStats> {
  return browserApi<CtiStats>(`/cti/stats/?academic_year_id=${academicYearId}`, { method: "GET" });
}
