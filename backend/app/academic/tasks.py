import logging
from datetime import date

from django_fsm import TransitionNotAllowed

from app.outgoing.tasks import enqueue_gale_shapley

from .models import AcademicYear

logger = logging.getLogger(__name__)


def auto_advance_recommendation_to_consolidation() -> None:
    """
    Tâche nocturne (minuit). Passe recommendation → consolidation dès que
    wishes_open_date est atteinte (début de la période de saisie des vœux).
    """
    today = date.today()
    qs = AcademicYear.objects.filter(
        status=AcademicYear.CampaignStatus.RECOMMENDATION,
        wishes_open_date__lte=today,
    )
    for year in qs:
        try:
            year.start_consolidation()
            year.save(update_fields=["status", "updated_at"])
            logger.info(
                "AcademicYear %s (%s) advanced: recommendation → consolidation",
                year.pk,
                year.label,
            )
        except TransitionNotAllowed:
            logger.warning(
                "AcademicYear %s (%s) transition recommendation → consolidation refused",
                year.pk,
                year.label,
            )


def auto_advance_consolidation_to_pre_assignment() -> None:
    """
    Tâche nocturne (23h59). Passe consolidation → pre_assignment dès que
    wishes_close_date est atteinte (fin de la période de saisie des vœux),
    puis lance automatiquement l'algorithme Gale-Shapley.
    """
    today = date.today()
    qs = AcademicYear.objects.filter(
        status=AcademicYear.CampaignStatus.CONSOLIDATION,
        wishes_close_date__lte=today,
    )
    for year in qs:
        try:
            year.launch_pre_assignment()
            year.save(update_fields=["status", "updated_at"])
            enqueue_gale_shapley(year.pk, triggered_by="auto")
            logger.info(
                "AcademicYear %s (%s) advanced: consolidation → pre_assignment"
                " — Gale-Shapley enqueued",
                year.pk,
                year.label,
            )
        except TransitionNotAllowed:
            logger.warning(
                "AcademicYear %s (%s) transition consolidation → pre_assignment refused",
                year.pk,
                year.label,
            )
