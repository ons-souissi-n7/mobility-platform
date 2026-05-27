from datetime import date, datetime
from typing import Any

from ninja import Schema

AGREEMENT_READONLY_FIELDS = frozenset(
    {
        "id",
        "reference",
        "moveon_relation_id",
        "direction",
        "status",
        "last_sync_moveon",
        "created_at",
        "updated_at",
        "start_date",
        "end_date",
        "framework",
    }
)


class AgreementSchema(Schema):
    name: str
    partner_university_id: int
    framework_ref_id: int | None = None
    is_active: bool = True
    remarks: str = ""
    id: int | None = None
    reference: str | None = None
    moveon_relation_id: str | None = None
    framework: str = ""
    direction: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    last_sync_moveon: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MobilityCategoryIn(Schema):
    name: str
    external_id: str = ""
    relation_types: str = ""
    is_active: bool = True


class MobilityCategoryOut(Schema):
    id: int
    moveon_framework_id: str
    external_id: str
    name: str
    relation_types: str
    is_active: bool
    last_sync_moveon: datetime | None
    created_at: datetime
    updated_at: datetime


class AgreementYearAvailabilityIn(Schema):
    agreement_id: int
    academic_year_id: int | None = None
    academic_year_label: str
    is_available: bool = True
    source: str = "manual"
    remarks: str = ""


class AgreementYearAvailabilityOut(AgreementYearAvailabilityIn):
    id: int
    created_at: datetime
    updated_at: datetime


class AgreementDepartmentConstraintIn(Schema):
    agreement_id: int
    department_id: int
    is_active: bool = True
    source: str = "manual"
    remarks: str = ""


class AgreementDepartmentConstraintOut(AgreementDepartmentConstraintIn):
    id: int
    created_at: datetime
    updated_at: datetime


class AgreementLevelConstraintIn(Schema):
    agreement_id: int
    level_id: int
    is_active: bool = True
    source: str = "manual"
    remarks: str = ""


class AgreementLevelConstraintOut(AgreementLevelConstraintIn):
    id: int
    created_at: datetime
    updated_at: datetime


class AgreementQuotaIn(Schema):
    agreement_id: int
    academic_year_label: str
    academic_year_id: int | None = None
    period: str = ""
    total_places: int = 0
    remaining_places: int = 0
    source_total_places: int | None = None
    remarks: str = ""
    source_institutions: str = ""


class AgreementQuotaOut(Schema):
    id: int
    agreement_id: int
    academic_year_id: int | None
    academic_year_label: str
    period: str
    places_id: str | None
    source_total_places: int | None
    source_remaining_places: int | None
    source_scope: str
    source_institutions: str
    total_places: int
    remaining_places: int
    allocated_places: int
    total_duration: int | None
    duration_unit: str
    is_effective: bool
    is_estimated: bool
    estimated_total_places: int | None = None
    is_validated: bool = False
    validated_by: str = ""
    validated_at: datetime | None = None
    estimation_basis: str
    remarks: str
    created_at: datetime
    updated_at: datetime


class AgreementQuotaValidateIn(Schema):
    validated_by: str = "Administrateur"


class DepartmentQuotaIn(Schema):
    agreement_quota_id: int
    department_id: int
    level_id: int | None = None
    places: int = 0
    is_estimated: bool = False
    estimation_basis: str = ""
    remarks: str = ""


class DepartmentQuotaOut(DepartmentQuotaIn):
    id: int
    estimated_places: int | None = None
    is_validated: bool
    validated_by: str
    validated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DepartmentQuotaValidateIn(Schema):
    validated_by: str = "Administrateur"


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
    agreement_id: int | None = None
    academic_year_id: int | None = None
    academic_year_label: str | None = None
    period: str | None = None
    total_places: int | None = None
    remaining_places: int | None = None
    total_duration: int | None = None
    duration_unit: str | None = None
