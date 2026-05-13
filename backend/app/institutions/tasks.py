from datetime import datetime, time, timedelta

from django.utils import timezone
from django_q.models import OrmQ, Schedule
from django_q.signing import SignedPackage
from django_q.tasks import async_task

SYNC_MOVEON_INSTITUTIONS_TASK = (
    "app.institutions.services.sync_moveon.sync_moveon_institutions"
)
SYNC_MOVEON_INSTITUTIONS_GROUP = "moveon-institutions-sync"
SYNC_MOVEON_INSTITUTIONS_TASK_NAME = "MoveON institutions sync"
SYNC_MOVEON_INSTITUTIONS_SCHEDULE_NAME = "MoveON institutions nightly sync"


def enqueue_sync_moveon_institutions() -> str:
    return async_task(
        SYNC_MOVEON_INSTITUTIONS_TASK,
        group=SYNC_MOVEON_INSTITUTIONS_GROUP,
        task_name=SYNC_MOVEON_INSTITUTIONS_TASK_NAME,
    )


def schedule_daily_sync_moveon_institutions(run_at: time) -> Schedule:
    next_run = get_next_run(run_at)
    schedule, _ = Schedule.objects.update_or_create(
        name=SYNC_MOVEON_INSTITUTIONS_SCHEDULE_NAME,
        defaults={
            "func": SYNC_MOVEON_INSTITUTIONS_TASK,
            "schedule_type": Schedule.DAILY,
            "repeats": -1,
            "next_run": next_run,
            "cluster": "mobility",
        },
    )
    schedule.full_clean()
    schedule.save()
    return schedule


def delete_scheduled_sync_moveon_institutions() -> int:
    deleted, _ = Schedule.objects.filter(
        name=SYNC_MOVEON_INSTITUTIONS_SCHEDULE_NAME
    ).delete()
    return deleted


def purge_pending_sync_moveon_institutions() -> int:
    deleted = 0

    for queued_task in OrmQ.objects.all():
        try:
            payload = SignedPackage.loads(queued_task.payload)
        except Exception:
            continue

        if payload.get("func") != SYNC_MOVEON_INSTITUTIONS_TASK:
            continue

        queued_task.delete()
        deleted += 1

    return deleted


def get_next_run(run_at: time):
    now = timezone.localtime()
    next_run = timezone.make_aware(
        datetime.combine(now.date(), run_at),
        timezone.get_current_timezone(),
    )

    if next_run <= now:
        next_run += timedelta(days=1)

    return next_run
