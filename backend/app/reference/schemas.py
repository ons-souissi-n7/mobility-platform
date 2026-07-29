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


class RawImportOut(Schema):
    id: int
    entity: str
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
    pegase_id: str | None = None
    last_sync_pegase: datetime | None = None
    is_terminal: bool = False


class LevelOut(LevelIn):
    id: int
    created_at: datetime
    updated_at: datetime


class ParcoursIn(Schema):
    department_id: int
    code: str
    label: str


class ParcoursOut(Schema):
    id: int
    department_id: int
    code: str
    label: str
