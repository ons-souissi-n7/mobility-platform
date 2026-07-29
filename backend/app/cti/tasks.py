import logging

from django_q.tasks import async_task

logger = logging.getLogger(__name__)


def enqueue_refresh_cti_durations(year_id: int, triggered_by: str = "") -> str:
    return async_task(
        "app.cti.tasks.run_refresh_cti_durations",
        year_id,
        triggered_by,
        group="cti-duration-refresh",
        task_name="CTI duration refresh",
    )


def run_refresh_cti_durations(year_id: int, triggered_by: str = "") -> None:
    from app.academic.models import AcademicYear
    from app.cti.services import refresh_cti_duration
    from app.cti.services_export import _get_terminal_enrolled

    try:
        academic_year = AcademicYear.objects.get(pk=year_id)
    except AcademicYear.DoesNotExist:
        logger.error("CTI duration refresh: year %d not found", year_id)
        return

    enrolled = _get_terminal_enrolled(academic_year)
    count = 0
    for enrollment in enrolled:
        refresh_cti_duration(enrollment.student)
        count += 1

    logger.info(
        "CTI duration refresh for year %s: %d students processed (triggered by %s)",
        academic_year.label,
        count,
        triggered_by or "système",
    )
