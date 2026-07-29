from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from .models import SystemAlert
from .schemas import SystemAlertOut

router = Router()


@router.get(
    "/",
    response=list[SystemAlertOut],
    summary="Lister les alertes non acquittées pour l'utilisateur courant",
)
def list_alerts(request):
    username = getattr(request.user, "username", None)
    alerts = list(
        SystemAlert.objects.filter(is_read=False)
        .exclude(academic_year__status="closed")
        .order_by("-created_at")
    )
    if username:
        alerts = [a for a in alerts if username not in (a.acknowledged_usernames or [])]
    return alerts


@router.post(
    "/{alert_id}/acknowledge/",
    response={204: None},
    summary="Acquitter une alerte pour l'utilisateur courant",
)
def acknowledge_alert(request, alert_id: int):
    try:
        alert = SystemAlert.objects.get(pk=alert_id, is_read=False)
    except SystemAlert.DoesNotExist as exc:
        raise HttpError(404, "Alerte introuvable.") from exc
    username = getattr(request.user, "username", None) or "unknown"
    if username not in (alert.acknowledged_usernames or []):
        alert.acknowledged_usernames = list(alert.acknowledged_usernames or []) + [
            username
        ]
        alert.save(update_fields=["acknowledged_usernames", "updated_at"])
    return 204, None


@router.post(
    "/{alert_id}/resolve/",
    response={204: None},
    summary="Résoudre globalement une alerte (la marque comme lue pour tous)",
)
def resolve_alert(request, alert_id: int):
    updated = SystemAlert.objects.filter(pk=alert_id, is_read=False).update(
        is_read=True,
        read_at=timezone.now(),
    )
    if not updated:
        raise HttpError(404, "Alerte introuvable.")
    return 204, None
