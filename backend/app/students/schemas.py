from datetime import datetime
from decimal import Decimal

from ninja import Schema


class ParcoursOut(Schema):
    id: int
    department_id: int
    code: str
    label: str


class AnnualEnrollmentOut(Schema):
    id: int
    academic_year_id: int
    department_id: int
    level_id: int
    parcours_id: int | None
    gpa: Decimal | None
    created_at: datetime
    updated_at: datetime


class StudentOut(Schema):
    id: int
    ine: str
    first_name: str
    last_name: str
    email: str
    gender: str
    created_at: datetime
    updated_at: datetime


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
