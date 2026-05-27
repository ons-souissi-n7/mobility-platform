from datetime import datetime
from typing import Any

from ninja import Schema


class CountryIn(Schema):
    iso2: str
    name_fr: str
    name_en: str
    cti_region: str


class CountryOut(Schema):
    id: int
    iso2: str
    name_fr: str
    name_en: str
    cti_region: str


class DepartmentIn(Schema):
    code: str
    name: str
    pegase_id: str | None = None


class DepartmentOut(Schema):
    id: int
    code: str
    name: str
    pegase_id: str | None
    last_sync_pegase: datetime | None


class DepartmentImportRetryIn(Schema):
    code: str | None = None
    name: str | None = None
    pegase_id: str | None = None


class DepartmentImportOut(Schema):
    id: int
    source: str
    source_file: str
    external_id: str
    payload: dict[str, Any]
    status: str
    error_message: str
    imported_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LevelIn(Schema):
    code: str
    name: str
    is_active: bool = True
    pegase_id: str | None = None
    last_sync_pegase: datetime | None = None


class LevelOut(LevelIn):
    id: int
    created_at: datetime
    updated_at: datetime


class LevelImportOut(Schema):
    id: int
    source: str
    source_file: str
    external_id: str
    payload: dict[str, Any]
    status: str
    error_message: str
    imported_at: datetime | None
    created_at: datetime
    updated_at: datetime
