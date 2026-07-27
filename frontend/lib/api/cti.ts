import { browserApi } from "@/lib/api/browser-client";

export type MobilityDuration = {
  ine: string;
  exchange_weeks: number;
  internship_weeks: number;
  complementary_weeks: number;
  total_weeks: number;
};

export type MobilityTotals = {
  exchange_weeks: number;
  internship_weeks: number;
  complementary_weeks: number;
  total_weeks: number;
};

export type ExchangeHistoryItem = {
  academic_year: string;
  institution_name: string;
  country_name: string;
  duration_weeks: number | null;
};

export type InternshipHistoryItem = {
  academic_year: string | null;
  company_name: string;
  country_name: string | null;
  start_date: string | null;
  end_date: string | null;
  weeks_in_company: number | null;
  is_international: boolean;
};

export type ComplementaryHistoryItem = {
  id: number;
  academic_year: string;
  experience_type: string;
  destination_country: string;
  destination_institution: string | null;
  start_date: string;
  end_date: string;
  duration_weeks: number;
  status: "pending" | "validated" | "rejected";
};

export type MobilityHistory = {
  ine: string;
  totals: MobilityTotals;
  exchanges: ExchangeHistoryItem[];
  internships: InternshipHistoryItem[];
  complementary_mobilities: ComplementaryHistoryItem[];
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
