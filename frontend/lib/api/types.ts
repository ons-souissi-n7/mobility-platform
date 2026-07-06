export type SystemAlert = {
  id: number;
  level: "warning" | "error";
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export type PagedResponse<T> = {
  count: number;
  page: number;
  page_size: number;
  results: T[];
};

export type SelectOption = {
  id: number;
  label: string;
};

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
  country_iso2: string;
  country_name_fr: string;
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
  inp_total_places: number;
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
  adjusted_places: number | null;
  effective_places: number;
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
  | "candidature"
  | "import"
  | "pre_assignment"
  | "validation"
  | "published"
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
  level_code: string | null;
  gpa: string | null;
  nationality_name_fr: string | null;
  is_alternant: boolean;
  is_scholarship: boolean;
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
  is_conflict?: boolean;
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
  closed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AssignmentStatus = "proposed" | "validated" | "published" | "cancelled";
export type SlotType = "dept" | "surplus" | "alternative" | "unassigned";

export type Assignment = {
  id: number;
  academic_year_id: number;
  academic_year_label: string;
  status: AssignmentStatus;
  run_by: string;
  total_students: number;
  assigned_count: number;
  unassigned_count: number;
  created_at: string;
};

export type AssignmentResult = {
  id: number;
  annual_enrollment_id: number;
  student_ine: string;
  student_last_name: string;
  student_first_name: string;
  department_code: string;
  agreement_year_id: number | null;
  agreement_name: string | null;
  university_name: string | null;
  slot_type: SlotType;
  assigned_rank: number | null;
  override_reason: string;
  override_agreement_year_id: number | null;
  override_agreement_id: number | null;
  override_agreement_name: string | null;
  override_university_name: string | null;
  override_slot_type: string | null;
  override_rank: number | null;
  source: "auto" | "override";
};

export type OverrideImportReport = {
  updated: number;
  skipped: number;
  errors: Array<{ ine: string; ligne: number; erreur: string }>;
};

export type AgreementYearOption = {
  id: number;
  label: string;
};

export type AssignmentDeptStat = {
  department_id: number;
  department_code: string;
  department_name: string;
  count: number;
};

export type AssignmentAgreementDeptStat = {
  dept_code: string;
  dept_name: string;
  quota: number;
  assigned: number;
};

export type AssignmentAgreementStat = {
  agreement_year_id: number;
  agreement_name: string;
  university_name: string;
  total_places: number;
  assigned: number;
  fill_rate: number;
  by_department: AssignmentAgreementDeptStat[];
};

export type AssignmentCountryStat = {
  country_name_fr: string;
  country_iso2: string;
  count: number;
};

export type AssignmentDeptCountryStat = {
  department_code: string;
  department_name: string;
  country_name_fr: string;
  country_iso2: string;
  count: number;
};

export type AssignmentStats = {
  total_students: number;
  assigned_count: number;
  unassigned_count: number;
  total_enrolled: number;
  by_slot_type: Record<string, number>;
  by_department: AssignmentDeptStat[];
  total_by_dept: Record<string, number>;
  by_agreement: AssignmentAgreementStat[];
  by_country: AssignmentCountryStat[];
  by_dept_country: AssignmentDeptCountryStat[];
};

export type StudentAssignment = {
  is_assigned: boolean;
  slot_type: string;
  university_name: string | null;
  country_name: string | null;
  agreement_name: string | null;
  effective_rank: number | null;
  override_reason: string | null;
};

export type EnrolledYear = {
  academic_year_id: number;
  academic_year_label: string;
  academic_year_status: string;
};

export type StudentProfile = {
  ine: string;
  first_name: string;
  last_name: string;
  email: string;
  enrolled_years: EnrolledYear[];
};

export type StudentAgreementDeptQuota = {
  department_id: number;
  department_code: string;
  effective_places: number;
};

export type StudentAgreement = {
  agreement_year_id: number;
  agreement_id: number;
  agreement_name: string;
  university_name: string;
  country_name: string;
  country_iso2: string;
  n7_places: number;
  dept_quotas: StudentAgreementDeptQuota[];
  valid_from: string | null;
  valid_until: string | null;
  direction: string;
};

export type StudentWishItem = {
  rank: number;
  agreement_year_id: number;
  agreement_name: string;
  university_name: string;
  country_name: string;
  country_iso2: string;
};
