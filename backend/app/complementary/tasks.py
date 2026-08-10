"""
Tâche Django-Q de purge RGPD des justificatifs expirés.

La tâche doit être planifiée via l'admin Django-Q ou le management command :
  python manage.py createschedule "purge_expired_documents" \
      "app.complementary.tasks.purge_expired_documents" \
      --schedule-type="D" --repeats=-1

Elle supprime de MinIO les fichiers dont le délai de conservation est dépassé
et vide le champ document_key correspondant en base.
"""

import datetime
import logging

from django.db.models import Q

logger = logging.getLogger(__name__)


def purge_expired_documents() -> int:
    """Supprime les justificatifs dont la date de rétention est dépassée.

    Retourne le nombre de fichiers supprimés.
    """
    from .models import ComplementaryMobility
    from .services.minio_service import delete_document

    today = datetime.date.today()
    expired = ComplementaryMobility.objects.filter(
        Q(document_retention_until__lt=today)
        & ~Q(document_key="")
        & Q(document_key__isnull=False)
    )

    count = 0
    for mob in expired:
        try:
            delete_document(mob.document_key)
            mob.document_key = ""
            mob.document_retention_until = None
            mob.save(
                update_fields=["document_key", "document_retention_until", "updated_at"]
            )
            count += 1
        except Exception as exc:
            logger.error(
                "Erreur suppression justificatif mobilité #%s : %s", mob.id, exc
            )

    if count:
        logger.info(
            "RGPD — %d justificatif(s) supprimé(s) après expiration de la rétention.",
            count,
        )

    return count
