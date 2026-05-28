from datetime import UTC, date, datetime, time

from auditlog.models import LogEntry
from ninja import Query, Router
from ninja.errors import HttpError

from .schemas import AuditLogOut

router = Router()

ACTION_LABELS = {
    LogEntry.Action.CREATE: "create",
    LogEntry.Action.UPDATE: "update",
    LogEntry.Action.DELETE: "delete",
    LogEntry.Action.ACCESS: "access",
}

ENTITY_TYPE_MODELS = {
    "academicyear": "academic",
    "agreement": "mobility",
    "agreementquota": "mobility",
}


def _serialize(entry: LogEntry) -> AuditLogOut:
    return AuditLogOut(
        id=entry.id,
        timestamp=entry.timestamp,
        actor_username=entry.actor.username if entry.actor_id else None,
        action=ACTION_LABELS.get(entry.action, str(entry.action)),
        entity_type=entry.content_type.model if entry.content_type_id else "",
        entity_id=entry.object_pk,
        entity_repr=entry.object_repr,
        changes=entry.changes,
    )


@router.get("/logs/", response=list[AuditLogOut], summary="Journal d'audit")
def list_audit_logs(
    request,
    entity_type: str | None = Query(None),  # noqa: B008
    action: str | None = Query(None),  # noqa: B008
    date_from: date | None = Query(None),  # noqa: B008
    date_to: date | None = Query(None),  # noqa: B008
    actor_username: str | None = Query(None),  # noqa: B008
):
    qs = LogEntry.objects.select_related("content_type", "actor").order_by("-timestamp")

    if entity_type:
        qs = qs.filter(content_type__model=entity_type.lower())

    if action:
        reverse_actions = {v: k for k, v in ACTION_LABELS.items()}
        action_code = reverse_actions.get(action.lower())
        if action_code is None:
            raise HttpError(400, f"Action invalide. Valeurs: {list(reverse_actions)}")
        qs = qs.filter(action=action_code)

    if date_from:
        qs = qs.filter(timestamp__gte=datetime.combine(date_from, time.min, tzinfo=UTC))

    if date_to:
        qs = qs.filter(timestamp__lte=datetime.combine(date_to, time.max, tzinfo=UTC))

    if actor_username:
        qs = qs.filter(actor__username__icontains=actor_username)

    return [_serialize(e) for e in qs]


@router.get("/logs/{log_id}/", response=AuditLogOut, summary="Detail d'un log d'audit")
def get_audit_log(request, log_id: int):
    try:
        entry = LogEntry.objects.select_related("content_type", "actor").get(pk=log_id)
    except LogEntry.DoesNotExist as exc:
        raise HttpError(404, "Log introuvable.") from exc
    return _serialize(entry)
