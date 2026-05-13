from datetime import time

from django.core.management.base import BaseCommand, CommandError

from app.institutions.services.sync_moveon import sync_moveon_institutions
from app.institutions.tasks import (
    delete_scheduled_sync_moveon_institutions,
    enqueue_sync_moveon_institutions,
    purge_pending_sync_moveon_institutions,
    schedule_daily_sync_moveon_institutions,
)


class Command(BaseCommand):
    help = "Synchronise les etablissements partenaires depuis l'API MoveON configuree."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Execute immediatement la synchronisation sans passer par Django Q2.",
        )
        parser.add_argument(
            "--clear-pending",
            action="store_true",
            help="Supprime les taches MoveON en attente dans la file Django Q2.",
        )
        parser.add_argument(
            "--schedule-daily",
            metavar="HH:MM",
            help="Planifie une synchronisation quotidienne a l'heure indiquee.",
        )
        parser.add_argument(
            "--delete-schedule",
            action="store_true",
            help="Supprime la planification quotidienne MoveON.",
        )

    def handle(self, *args, **options):
        if options["clear_pending"]:
            deleted = purge_pending_sync_moveon_institutions()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {deleted} pending MoveON institutions sync task(s)."
                )
            )
            return

        if options["delete_schedule"]:
            deleted = delete_scheduled_sync_moveon_institutions()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {deleted} scheduled MoveON institutions sync(s)."
                )
            )
            return

        if options["schedule_daily"]:
            try:
                run_at = parse_hhmm(options["schedule_daily"])
            except ValueError as exc:
                raise CommandError(str(exc)) from exc
            schedule = schedule_daily_sync_moveon_institutions(run_at)
            self.stdout.write(
                self.style.SUCCESS(
                    "MoveON institutions sync scheduled daily: "
                    f"name={schedule.name}, next_run={schedule.next_run}"
                )
            )
            return

        if not options["sync"]:
            task_id = enqueue_sync_moveon_institutions()
            self.stdout.write(
                self.style.SUCCESS(
                    "MoveON institutions sync queued with Django Q2: "
                    f"task_id={task_id}"
                )
            )
            return

        result = sync_moveon_institutions()
        self.stdout.write(
            self.style.SUCCESS(
                "MoveON institutions sync completed: "
                f"total={result.total}, created={result.created}, "
                f"updated={result.updated}, failed={result.failed}, "
                f"ignored={result.ignored}"
            )
        )


def parse_hhmm(value):
    try:
        hour_text, minute_text = value.split(":", maxsplit=1)
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError as exc:
        raise ValueError("Expected time format HH:MM.") from exc

    if hour not in range(24) or minute not in range(60):
        raise ValueError("Expected time format HH:MM.")

    return time(hour=hour, minute=minute)
