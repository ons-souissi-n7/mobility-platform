from datetime import datetime

from ninja import Schema


class AuditLogOut(Schema):
    id: int
    timestamp: datetime
    actor_username: str | None
    action: str
    entity_type: str
    entity_id: str
    entity_repr: str
    changes: dict | None
