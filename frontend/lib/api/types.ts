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
  pegase_id: string | null;
  last_sync_pegase: string | null;
  updated_at: string;
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
  entity?: string;
  external_id: string;
  payload: Record<string, unknown>;
  status: string;
  error_message: string;
  imported_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Agreement = {
  id: number | null;
  name: string;
  partner_university_id: number;
  framework_ref_id: number | null;
  is_active: boolean;
  remarks: string;
  // Read-only — server/MoveON managed
  framework: string;
  reference: string | null;
  moveon_relation_id: string | null;
  direction: string | null;
  status: string | null;
  start_date: string | null;
  end_date: string | null;
  last_sync_moveon: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type MobilityCategory = {
  id: number;
  moveon_framework_id: string;
  external_id: string;
  name: string;
  relation_types: string;
  is_active: boolean;
  last_sync_moveon: string | null;
  created_at: string;
  updated_at: string;
};

export type Level = {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
  pegase_id: string | null;
  last_sync_pegase: string | null;
  created_at: string;
  updated_at: string;
};

export type AgreementYearAvailability = {
  id: number;
  agreement_id: number;
  academic_year_id: number | null;
  academic_year_label: string;
  is_available: boolean;
  source: string;
  remarks: string;
  created_at: string;
  updated_at: string;
};

export type AgreementDepartmentConstraint = {
  id: number;
  agreement_id: number;
  department_id: number;
  is_active: boolean;
  source: string;
  remarks: string;
  created_at: string;
  updated_at: string;
};

export type AgreementLevelConstraint = {
  id: number;
  agreement_id: number;
  level_id: number;
  is_active: boolean;
  source: string;
  remarks: string;
  created_at: string;
  updated_at: string;
};

export type AgreementQuota = {
  id: number;
  agreement_id: number;
  academic_year_id: number | null;
  academic_year_label: string;
  period: string;
  places_id: string | null;
  source_total_places: number | null;
  source_remaining_places: number | null;
  source_scope: string;
  source_institutions: string;
  total_places: number;
  remaining_places: number;
  allocated_places: number;
  total_duration: number | null;
  duration_unit: string;
  is_effective: boolean;
  is_estimated: boolean;
  estimated_total_places: number | null;
  is_validated: boolean;
  validated_by: string;
  validated_at: string | null;
  estimation_basis: string;
  remarks: string;
  created_at: string;
  updated_at: string;
};

export type DepartmentQuota = {
  id: number;
  agreement_quota_id: number;
  department_id: number;
  level_id: number | null;
  places: number;
  estimated_places: number | null;
  is_estimated: boolean;
  is_validated: boolean;
  validated_by: string;
  validated_at: string | null;
  estimation_basis: string;
  remarks: string;
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
  closed_at: string | null;
  created_at: string;
  updated_at: string;
};
