from datetime import datetime
from decimal import Decimal

from ninja import Schema  # noqa: I001


class ParcoursOut(Schema):
    id: int
    department_id: int
    code: str
    label: str


class AnnualEnrollmentOut(Schema):
    id: int
    academic_year_id: int
    academic_year_label: str
    department_id: int
    department_code: str
    level_id: int
    level_code: str
    parcours_id: int | None
    parcours_code: str | None
    gpa: Decimal | None
    is_alternant: bool
    is_scholarship: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_academic_year_label(obj) -> str:
        return obj.academic_year.label

    @staticmethod
    def resolve_department_code(obj) -> str:
        return obj.department.code

    @staticmethod
    def resolve_level_code(obj) -> str:
        return obj.level.code

    @staticmethod
    def resolve_parcours_code(obj) -> str | None:
        return obj.parcours.code if obj.parcours_id else None


class StudentOut(Schema):
    id: int
    ine: str
    first_name: str
    last_name: str
    email: str
    gender: str
    nationality_iso2: str | None = None
    nationality_name_fr: str | None = None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_nationality_iso2(obj) -> str | None:
        return obj.nationality.iso2 if obj.nationality_id else None

    @staticmethod
    def resolve_nationality_name_fr(obj) -> str | None:
        return obj.nationality.name_fr if obj.nationality_id else None


class StudentDetailOut(StudentOut):
    enrollments: list[AnnualEnrollmentOut]


class ImportReportOut(Schema):
    created: int
    updated: int
    unresolved: list[dict]
    errors: list[str]


class StudentRawImportOut(Schema):
    id: int
    entity: str
    source: str
    source_file: str
    external_id: str
    payload: dict
    status: str
    error_message: str
    imported_at: datetime | None
    created_at: datetime
    updated_at: datetime


# -- Stats per academic year ------------------------------------------------


class LevelStatOut(Schema):
    level_id: int
    level_code: str
    level_name: str
    count: int


class DepartmentStatOut(Schema):
    department_id: int
    department_code: str
    department_name: str
    count: int


class ParcoursStatOut(Schema):
    parcours_id: int | None
    parcours_code: str | None
    parcours_label: str | None
    count: int


class CrossStatOut(Schema):
    level_id: int
    level_code: str
    level_name: str
    department_id: int
    department_code: str
    department_name: str
    parcours_id: int | None
    parcours_code: str | None
    parcours_label: str | None
    count: int


class StudentStatsOut(Schema):
    total: int
    by_level: list[LevelStatOut]
    by_department: list[DepartmentStatOut]
    by_parcours: list[ParcoursStatOut]
    cross: list[CrossStatOut]


# -- Student list with enrollment for a specific year -----------------------


class StudentEnrollmentOut(Schema):
    student_id: int
    ine: str
    first_name: str
    last_name: str
    email: str
    gender: str
    nationality_iso2: str | None
    nationality_name_fr: str | None
    department_id: int
    department_code: str
    department_name: str
    level_id: int
    level_code: str
    level_name: str
    parcours_id: int | None
    parcours_code: str | None
    parcours_label: str | None
    gpa: Decimal | None
    is_alternant: bool
    is_scholarship: bool


class StudentImportRetryIn(Schema):
    department_id: int | None = None
    level_id: int | None = None
    parcours_id: int | None = None
