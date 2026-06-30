import logging
from datetime import date, timedelta

from django_fsm import TransitionNotAllowed

from app.audit.logger import log_action
from app.outgoing.tasks import enqueue_gale_shapley

from .models import AcademicYear

logger = logging.getLogger(__name__)


def _add_one_year(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        # 29 fév dans une année bissextile → 28 fév l'année suivante
        return d.replace(year=d.year + 1, day=28)


def auto_create_next_academic_year() -> None:
    """
    Tâche nocturne (minuit). Pour chaque année dont end_date = hier et qui vient
    d'être clôturée (à 23h59 la veille), crée automatiquement l'année suivante en
    décalant toutes les dates d'un an.
    La nouvelle année est créée en statut INITIALIZATION et peut être modifiée manuellement.
    """
    yesterday = date.today() - timedelta(days=1)
    qs = AcademicYear.objects.filter(
        status=AcademicYear.CampaignStatus.CLOSED,
        end_date=yesterday,
    )
    for year in qs:
        new_start = _add_one_year(year.start_date)
        new_end = _add_one_year(year.end_date)
        new_label = f"{new_start.year}-{new_end.year}"

        if AcademicYear.objects.filter(label=new_label).exists():
            logger.info(
                "AcademicYear %s already exists, skipping auto-creation",
                new_label,
            )
            continue

        new_year = AcademicYear(
            label=new_label,
            start_date=new_start,
            end_date=new_end,
            wishes_open_date=_add_one_year(year.wishes_open_date)
            if year.wishes_open_date
            else None,
            wishes_close_date=_add_one_year(year.wishes_close_date)
            if year.wishes_close_date
            else None,
        )
        new_year.full_clean()
        new_year.save()
        logger.info(
            "AcademicYear %s created automatically (next year after %s)",
            new_label,
            year.label,
        )
        log_action(
            action="auto_create_academic_year",
            detail=f"Année {new_label} créée automatiquement après clôture de {year.label}.",
        )


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
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — transition recommendation → consolidation refusée.",
            )


def auto_close_academic_year() -> None:
    """
    Tâche nocturne (23h59). Clôture automatiquement les années universitaires
    dont la date de fin est atteinte et dont l'affectation a été publiée
    (statut VALIDATION → CLOSED).
    """
    today = date.today()
    qs = AcademicYear.objects.filter(
        status=AcademicYear.CampaignStatus.VALIDATION,
        end_date__lte=today,
    )
    for year in qs:
        try:
            year.close()
            year.save(update_fields=["status", "closed_at", "updated_at"])
            logger.info(
                "AcademicYear %s (%s) closed automatically at end_date",
                year.pk,
                year.label,
            )
        except TransitionNotAllowed:
            logger.warning(
                "AcademicYear %s (%s) transition validation → closed refused",
                year.pk,
                year.label,
            )
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — transition validation → closed refusée.",
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
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — transition consolidation → pre_assignment refusée.",
            )
