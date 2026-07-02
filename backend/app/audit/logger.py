"""
Utilitaire pour journaliser des actions qui ne passent pas
par un save() de modèle (syncs, imports batch, uploads...).

Usage:
    from app.audit.logger import log_action
    log_action(request, action="sync_moveon", detail="30 accords mis à jour")
"""

from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType


def log_action(
    request=None,
    *,
    action: str,
    detail: str = "",
) -> None:
    """
    Crée une entrée de log pour une action non liée à un save() de modèle.
    Utilisé pour : sync, import batch, upload, relance d'erreur, tâches de fond, etc.
    request peut être None pour les tâches asynchrones sans contexte HTTP.
    """
    actor = None
    if request is not None:
        actor = getattr(request, "user", None)
        if actor is not None and not actor.is_authenticated:
            actor = None

    ct = ContentType.objects.get_for_model(LogEntry)

    LogEntry.objects.create(
        content_type=ct,
        object_pk="0",
        object_repr=action,
        action=LogEntry.Action.ACCESS,
        actor=actor,
        changes={"action": [None, action], "detail": [None, detail]},
    )
