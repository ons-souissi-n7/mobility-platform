from datetime import date, datetime
from typing import Any

from ninja import Schema

AGREEMENT_READONLY_FIELDS = frozenset(
    {
        "id",
        "moveon_id",
        "last_sync_moveon",
        "created_at",
        "updated_at",
    }
)

AGREEMENT_YEAR_READONLY_FIELDS = frozenset(
    {
        "id",
        "is_validated",
        "validated_by",
        "validated_at",
        "created_at",
        "updated_at",
    }
)


class AgreementIn(Schema):
    name: str
    partner_university_id: int
    category_id: int | None = None
    direction: str = "unknown"
    valid_from: date | None = None
    valid_until: date | None = None
    inp_total_places: int = 0
    inp_institutions: str = ""
    remarks: str = ""
    level_ids: list[int] = []


class AgreementOut(Schema):
    id: int
    moveon_id: str | None
    name: str
    partner_university_id: int
    category_id: int | None
    direction: str
    valid_from: date | None
    valid_until: date | None
    inp_total_places: int
    inp_institutions: str
    remarks: str
    last_sync_moveon: datetime | None
    level_ids: list[int]
    department_ids: list[int]
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_department_ids(obj) -> list[int]:
        return list(obj.agreement_departments.values_list("department_id", flat=True))


class AgreementDepartmentIn(Schema):
    agreement_id: int
    department_id: int
    remarks: str = ""


class AgreementDepartmentOut(Schema):
    id: int
    agreement_id: int
    department_id: int
    remarks: str
    created_at: datetime
    updated_at: datetime


class AgreementYearIn(Schema):
    agreement_id: int
    academic_year_id: int
    is_active: bool = True
    n7_places: int = 0


class AgreementYearOut(Schema):
    id: int
    agreement_id: int
    academic_year_id: int
    academic_year_label: str
    is_active: bool
    n7_places: int
    is_validated: bool
    validated_by: str
    validated_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgreementYearValidateIn(Schema):
    validated_by: str = "Administrateur"


class AgreementYearDepartmentIn(Schema):
    agreement_year_id: int
    department_id: int
    estimated_places: int = 0


class AgreementYearDepartmentOut(Schema):
    id: int
    agreement_year_id: int
    agreement_department_id: int
    department_id: int
    estimated_places: int
    adjusted_places: int | None
    effective_places: int
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_department_id(obj) -> int:
        return obj.agreement_department.department_id

    @staticmethod
    def resolve_effective_places(obj) -> int:
        return obj.get_effective_quota()


class MobilityCategoryIn(Schema):
    name: str


class MobilityCategoryOut(Schema):
    id: int
    moveon_id: str | None
    name: str
    last_sync_moveon: datetime | None
    created_at: datetime
    updated_at: datetime


class RawImportOut(Schema):
    id: int
    source: str
    source_file: str
    entity: str
    external_id: str
    payload: dict[str, Any]
    status: str
    error_message: str
    imported_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RawImportRetryIn(Schema):
    partner_university_id: int | None = None
