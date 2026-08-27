import logging
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)

# Commandes qui démarrent réellement le serveur ou le worker Django-Q et ont
# donc besoin des schedules synchronisés. Les autres (check, makemigrations,
# test, shell, ...) n'ont pas besoin d'accès à la base au chargement des apps.
_COMMANDS_REQUIRING_SCHEDULE_SYNC = {"runserver", "qcluster"}


class AcademicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.academic"

    def ready(self) -> None:
        if len(sys.argv) < 2 or sys.argv[1] not in _COMMANDS_REQUIRING_SCHEDULE_SYNC:
            return

        from django.db import connection

        # Synchronise les schedules Django Q au démarrage du serveur.
        # Évite d'avoir à lancer register_academic_schedules manuellement après chaque deploy.
        try:
            if "django_q_schedule" in connection.introspection.table_names():
                from app.academic.management.commands.register_academic_schedules import (
                    Command,
                )

                Command().sync_schedules()
        except Exception:
            logger.exception(
                "Échec de la synchronisation des schedules Django-Q au démarrage"
            )
