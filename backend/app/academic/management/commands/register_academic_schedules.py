import logging

from django.core.management.base import BaseCommand
from django_q.models import Schedule

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Enregistre les tâches planifiées de transition automatique FSM des années universitaires."

    SCHEDULES = [
        {
            "name": "academic_create_next_year",
            "func": "app.academic.tasks.auto_create_next_academic_year",
            "cron": "0 0 * * *",
            "note": "création année suivante à minuit (lendemain de la clôture)",
        },
        {
            "name": "academic_start_candidature",
            "func": "app.academic.tasks.auto_advance_recommendation_to_candidature",
            "cron": "0 0 * * *",
            "note": "recommendation → candidature à minuit (ouverture des vœux)",
        },
        {
            "name": "academic_close_wishes",
            "func": "app.academic.tasks.auto_close_wishes",
            "cron": "59 23 * * *",
            "note": "candidature → import à 23h59 (clôture des vœux)",
        },
        {
            "name": "academic_close_at_end_date",
            "func": "app.academic.tasks.auto_close_academic_year",
            "cron": "59 23 * * *",
            "note": "published → closed à 23h59 (end_date atteinte)",
        },
    ]

    def sync_schedules(self) -> None:
        known_names = {s["name"] for s in self.SCHEDULES}
        for s in self.SCHEDULES:
            Schedule.objects.update_or_create(
                name=s["name"],
                defaults={
                    "func": s["func"],
                    "schedule_type": Schedule.CRON,
                    "cron": s["cron"],
                },
            )
        deleted, _ = (
            Schedule.objects.filter(name__startswith="academic_")
            .exclude(name__in=known_names)
            .delete()
        )
        if deleted:
            logger.info("Supprimé %d schedule(s) académique(s) orphelin(s)", deleted)

    def handle(self, *_args, **_options):
        self.sync_schedules()
        for s in self.SCHEDULES:
            self.stdout.write(f"OK : {s['name']} — {s['note']}")
        self.stdout.write(self.style.SUCCESS("Planification FSM enregistrée."))
