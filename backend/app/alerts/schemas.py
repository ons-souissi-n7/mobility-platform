from datetime import datetime

from ninja import Schema


class SystemAlertOut(Schema):
    id: int
    level: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
