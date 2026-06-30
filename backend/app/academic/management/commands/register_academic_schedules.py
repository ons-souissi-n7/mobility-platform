from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Enregistre les tâches planifiées de transition automatique FSM des années universitaires."

    SCHEDULES = [
        {
            "name": "academic_create_next_year",
            "func": "app.academic.tasks.auto_create_next_academic_year",
            "cron": "0 0 * * *",
            "note": "création automatique de l'année suivante à minuit après clôture",
        },
        {
            "name": "academic_recommendation_to_consolidation",
            "func": "app.academic.tasks.auto_advance_recommendation_to_consolidation",
            "cron": "0 0 * * *",
            "note": "recommendation → consolidation à minuit (ouverture des vœux)",
        },
        {
            "name": "academic_consolidation_to_pre_assignment",
            "func": "app.academic.tasks.auto_advance_consolidation_to_pre_assignment",
            "cron": "59 23 * * *",
            "note": "consolidation → pre_assignment à 23h59 (clôture des vœux) + Gale-Shapley",
        },
        {
            "name": "academic_close_at_end_date",
            "func": "app.academic.tasks.auto_close_academic_year",
            "cron": "59 23 * * *",
            "note": "validation → closed à 23h59 le jour de end_date",
        },
    ]

    def handle(self, *args, **options):
        for s in self.SCHEDULES:
            obj, created = Schedule.objects.update_or_create(
                name=s["name"],
                defaults={
                    "func": s["func"],
                    "schedule_type": Schedule.CRON,
                    "cron": s["cron"],
                },
            )
            verb = "Créé" if created else "Mis à jour"
            self.stdout.write(f"{verb} : {s['name']} — {s['note']}")

        self.stdout.write(self.style.SUCCESS("Planification FSM enregistrée."))
