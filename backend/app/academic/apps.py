from django.apps import AppConfig


class AcademicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.academic"

    def ready(self) -> None:
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
            pass
