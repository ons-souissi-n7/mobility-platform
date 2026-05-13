from datetime import datetime
from typing import Any

from ninja import Schema


class PartnerUniversityIn(Schema):
    moveon_id: int | None = None
    name: str
    short_name: str = ""
    translated_name: str = ""
    erasmus_code: str = ""
    city: str = ""
    url: str = ""
    email: str = ""
    country_id: int
    last_sync_moveon: datetime | None = None


class PartnerUniversityOut(Schema):
    id: int
    moveon_id: int | None
    name: str
    short_name: str
    translated_name: str
    erasmus_code: str
    city: str
    url: str
    email: str
    country_id: int
    last_sync_moveon: datetime | None
    created_at: datetime
    updated_at: datetime


class PartnerUniversityImportRetryIn(Schema):
    country_id: int | None = None
    country_iso2: str | None = None
    country_name: str | None = None


class PartnerUniversityImportOut(Schema):
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
