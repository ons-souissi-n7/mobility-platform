from datetime import datetime
from decimal import Decimal

from ninja import Schema


class AssignmentResultOut(Schema):
    id: int
    annual_enrollment_id: int
    student_ine: str
    student_last_name: str
    student_first_name: str
    department_code: str
    agreement_year_id: int | None
    agreement_name: str | None
    university_name: str | None
    slot_type: str
    assigned_rank: int | None
    override_reason: str

    @staticmethod
    def resolve_student_ine(obj) -> str:
        return obj.annual_enrollment.student.ine

    @staticmethod
    def resolve_student_last_name(obj) -> str:
        return obj.annual_enrollment.student.last_name

    @staticmethod
    def resolve_student_first_name(obj) -> str:
        return obj.annual_enrollment.student.first_name

    @staticmethod
    def resolve_department_code(obj) -> str:
        return obj.annual_enrollment.department.code

    @staticmethod
    def resolve_agreement_name(obj) -> str | None:
        return obj.agreement_year.agreement.name if obj.agreement_year_id else None

    @staticmethod
    def resolve_university_name(obj) -> str | None:
        if obj.agreement_year_id:
            return obj.agreement_year.agreement.partner_university.name
        return None


class AssignmentAgreementDeptStat(Schema):
    dept_code: str
    dept_name: str
    quota: int
    assigned: int


class AssignmentAgreementStat(Schema):
    agreement_year_id: int
    agreement_name: str
    university_name: str
    total_places: int
    assigned: int
    fill_rate: float
    by_department: list[AssignmentAgreementDeptStat]


class AssignmentStatsOut(Schema):
    total_students: int
    assigned_count: int
    unassigned_count: int
    by_slot_type: dict[str, int]
    by_department: list[dict]
    by_agreement: list[AssignmentAgreementStat]
    by_country: list[dict]
    by_dept_country: list[dict]


class AssignmentOut(Schema):
    id: int
    academic_year_id: int
    academic_year_label: str
    status: str
    run_by: str
    total_students: int
    assigned_count: int
    unassigned_count: int
    created_at: datetime

    @staticmethod
    def resolve_academic_year_label(obj) -> str:
        return obj.academic_year.label


# ── Vœux sortants ─────────────────────────────────────────────────────────────


class AgreementWishOut(Schema):
    rank: int
    agreement_id: int
    moveon_id: str | None
    agreement_name: str
    university_name: str
    direction: str


class StudentWishesOut(Schema):
    student_id: int
    ine: str
    first_name: str
    last_name: str
    department_code: str | None
    parcours_code: str | None
    gpa: Decimal | None
    nationality_name_fr: str | None
    wishes: list[AgreementWishOut]


class WishSyncReportOut(Schema):
    created: int
    updated: int
    skipped: int
    total: int
    unresolved: list[dict]
    errors: list[str]


class WishImportRetryIn(Schema):
    student_id: int | None = None
    agreement_id: int | None = None
