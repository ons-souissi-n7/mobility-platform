from datetime import datetime

from ninja import Schema


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
