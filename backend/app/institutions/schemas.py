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
    country_iso2: str
    country_name_fr: str
    last_sync_moveon: datetime | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_country_iso2(obj) -> str:
        return obj.country.iso2 if obj.country_id else ""

    @staticmethod
    def resolve_country_name_fr(obj) -> str:
        return obj.country.name_fr if obj.country_id else ""


class PartnerUniversityImportRetryIn(Schema):
    country_id: int | None = None
    country_iso2: str | None = None
    country_name: str | None = None
    name: str | None = None
    short_name: str | None = None
    translated_name: str | None = None
    erasmus_code: str | None = None
    city: str | None = None
    url: str | None = None
    email: str | None = None


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
