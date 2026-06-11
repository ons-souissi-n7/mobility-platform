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
  id: number;
  moveon_id: string | null;
  reference: string;
  name: string;
  partner_university_id: number;
  category_id: number | null;
  direction: string;
  valid_from: string | null;
  valid_until: string | null;
  inp_total_places: number;
  inp_institutions: string;
  remarks: string;
  department_ids: number[];
  level_ids: number[];
  last_sync_moveon: string | null;
  created_at: string;
  updated_at: string;
};

export type AgreementYear = {
  id: number;
  agreement_id: number;
  academic_year_id: number;
  academic_year_label: string;
  is_active: boolean;
  n7_places: number;
  is_validated: boolean;
  validated_by: string;
  validated_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AgreementYearDepartment = {
  id: number;
  agreement_year_id: number;
  department_id: number;
  estimated_places: number;
  created_at: string;
  updated_at: string;
};

export type MobilityCategory = {
  id: number;
  moveon_id: string | null;
  name: string;
  last_sync_moveon: string | null;
  created_at: string;
  updated_at: string;
};

export type Level = {
  id: number;
  code: string;
  name: string;
  pegase_id: string | null;
  last_sync_pegase: string | null;
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

export type Parcours = {
  id: number;
  department_id: number;
  code: string;
  label: string;
};

export type AnnualEnrollment = {
  id: number;
  academic_year_id: number;
  academic_year_label: string;
  department_id: number;
  department_code: string;
  level_id: number;
  level_code: string;
  parcours_id: number | null;
  parcours_code: string | null;
  gpa: string | null;
  created_at: string;
  updated_at: string;
};

export type Student = {
  id: number;
  ine: string;
  first_name: string;
  last_name: string;
  email: string;
  gender: string;
  nationality_iso2: string | null;
  nationality_name_fr: string | null;
  pegase_id: string | null;
  created_at: string;
  updated_at: string;
};

export type StudentDetail = Student & {
  enrollments: AnnualEnrollment[];
};

export type ImportReport = {
  created: number;
  updated: number;
  unresolved: Record<string, string>[];
  errors: string[];
};

export type LevelStat = {
  level_id: number;
  level_code: string;
  level_name: string;
  count: number;
};

export type DepartmentStat = {
  department_id: number;
  department_code: string;
  department_name: string;
  count: number;
};

export type ParcoursStat = {
  parcours_id: number | null;
  parcours_code: string | null;
  parcours_label: string | null;
  count: number;
};

export type CrossStat = {
  level_id: number;
  level_code: string;
  level_name: string;
  department_id: number;
  department_code: string;
  department_name: string;
  parcours_id: number | null;
  parcours_code: string | null;
  parcours_label: string | null;
  count: number;
};

export type StudentStats = {
  total: number;
  by_level: LevelStat[];
  by_department: DepartmentStat[];
  by_parcours: ParcoursStat[];
  cross: CrossStat[];
};

export type StudentWithEnrollment = {
  student_id: number;
  ine: string;
  first_name: string;
  last_name: string;
  email: string;
  gender: string;
  nationality_iso2: string | null;
  nationality_name_fr: string | null;
  department_id: number;
  department_code: string;
  department_name: string;
  level_id: number;
  level_code: string;
  level_name: string;
  parcours_id: number | null;
  parcours_code: string | null;
  parcours_label: string | null;
  gpa: string | null;
};

export type AgreementWish = {
  rank: number;
  agreement_id: number;
  moveon_id: string | null;
  agreement_name: string;
  university_name: string;
  direction: string;
};

export type StudentWishes = {
  student_id: number;
  ine: string;
  first_name: string;
  last_name: string;
  department_code: string | null;
  parcours_code: string | null;
  gpa: string | null;
  wishes: AgreementWish[];
};

export type WishSyncReport = {
  created: number;
  updated: number;
  skipped: number;
  total: number;
  unresolved: Record<string, string>[];
  errors: string[];
};

export type AuditLog = {
  id: number;
  timestamp: string;
  actor_username: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  entity_repr: string;
  changes: Record<string, [unknown, unknown]> | null;
};

export type ImportErrorItem = {
  external_id: string;
  reason: string;
  raw_import_id: number | null;
};

export type ImportReportList = {
  id: number;
  source: string;
  source_display: string;
  academic_year_id: number | null;
  academic_year_label: string | null;
  total: number;
  success_count: number;
  error_count: number;
  duplicate_count: number;
  triggered_by: string;
  created_at: string;
};

export type ImportReportDetail = ImportReportList & {
  errors: ImportErrorItem[];
  updated_at: string;
};

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
