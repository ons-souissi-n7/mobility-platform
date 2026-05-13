export type Country = {
  id: number;
  iso2: string;
  name_fr: string;
  name_en: string;
  cti_region: string;
};

export type Department = {
  id: number;
  code: string;
  name: string;
};

export type PartnerUniversity = {
  id: number;
  moveon_id: number | null;
  name: string;
  short_name: string;
  translated_name: string;
  erasmus_code: string;
  city: string;
  url: string;
  email: string;
  country_id: number;
  last_sync_moveon: string | null;
  created_at: string;
  updated_at: string;
};

export type RawImport = {
  id: number;
  source: string;
  source_file: string;
  external_id: string;
  payload: Record<string, unknown>;
  status: string;
  error_message: string;
  imported_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AcademicYearStatus =
  | "initialization"
  | "recommendation"
  | "consolidation"
  | "pre_assignment"
  | "validation"
  | "closed";

export type AcademicYear = {
  id: number;
  label: string;
  start_date: string;
  end_date: string;
  status: AcademicYearStatus;
  wishes_open_date: string | null;
  wishes_close_date: string | null;
  gpa_freeze_date: string | null;
  results_publication_date: string | null;
  created_at: string;
  updated_at: string;
};
