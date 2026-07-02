import logging
from datetime import date, timedelta

from django_fsm import TransitionNotAllowed

from app.alerts.models import SystemAlert
from app.audit.logger import log_action

from .models import AcademicYear

logger = logging.getLogger(__name__)


def _alert_transition_failed(
    year: AcademicYear, expected_state: str, to_state: str
) -> None:
    title = f"Transition automatique échouée — {year.label}"
    message = (
        f"La tâche programmée n'a pas pu faire passer l'année {year.label} "
        f"vers l'état « {to_state} ». "
        f"L'état attendu était « {expected_state} » "
        f"mais l'année est actuellement en état « {year.status} ». "
        f"La transition a été annulée. Une intervention manuelle est nécessaire."
    )
    SystemAlert.objects.create(level="error", title=title, message=message)


def _alert_transition_failed_close(year: AcademicYear) -> None:
    """Alerte de clôture avec message contextuel selon l'état de l'année."""
    if year.status == AcademicYear.CampaignStatus.VALIDATION:
        hint = (
            "L'affectation est en cours de validation — publiez les résultats "
            "avant que la clôture automatique puisse s'exécuter."
        )
    elif year.status == AcademicYear.CampaignStatus.PRE_ASSIGNMENT:
        hint = (
            "L'algorithme d'affectation n'a pas encore terminé. "
            "Vérifiez les logs Celery et relancez le calcul si nécessaire."
        )
    else:
        hint = f"L'état actuel est « {year.status} »."

    title = f"Clôture automatique impossible — {year.label}"
    message = (
        f"La date de fin de l'année {year.label} est dépassée, "
        f"mais la clôture automatique (published → closed) ne peut pas s'exécuter. "
        f"{hint}"
    )
    SystemAlert.objects.create(level="error", title=title, message=message)


def _add_one_year(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        return d.replace(year=d.year + 1, day=28)


def auto_create_next_academic_year() -> None:
    """
    Tâche nocturne. Pour chaque année clôturée dont end_date = hier,
    crée automatiquement l'année suivante en décalant toutes les dates d'un an.
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

        defaults = {
            "start_date": new_start,
            "end_date": new_end,
            "wishes_open_date": _add_one_year(year.wishes_open_date)
            if year.wishes_open_date
            else None,
            "wishes_close_date": _add_one_year(year.wishes_close_date)
            if year.wishes_close_date
            else None,
        }
        new_year, created = AcademicYear.objects.get_or_create(
            label=new_label, defaults=defaults
        )
        if not created:
            logger.info(
                "AcademicYear %s already exists, skipping auto-creation", new_label
            )
            continue
        new_year.full_clean()
        logger.info(
            "AcademicYear %s created automatically (next year after %s)",
            new_label,
            year.label,
        )

        # Initialiser les accords de mobilité pour la nouvelle année
        from app.mobility.services.quota_estimator import initialize_new_year_mobility

        mob_detail = ""
        try:
            mob_result = initialize_new_year_mobility(new_year)
            mob_detail = f" Mobilité : {mob_result.year_instances_created} accords-années initialisés."
            logger.info(
                "Mobilité initialisée pour %s : %d accords traités, %d AgreementYear créés",
                new_label,
                mob_result.agreements_processed,
                mob_result.year_instances_created,
            )
        except Exception:
            logger.exception(
                "Erreur lors de l'initialisation de la mobilité pour %s — "
                "initialisation manuelle requise",
                new_label,
            )
            SystemAlert.objects.create(
                level="error",
                title=f"Initialisation mobilité échouée — {new_label}",
                message=(
                    f"L'année {new_label} a été créée automatiquement mais "
                    f"l'initialisation des accords de mobilité a échoué. "
                    f"Lancez l'initialisation manuellement depuis Mobilité > Initialiser l'année."
                ),
            )

        log_action(
            action="auto_create_academic_year",
            detail=(
                f"Année {new_label} créée automatiquement après clôture de {year.label}."
                + mob_detail
            ),
        )


def auto_advance_recommendation_to_candidature() -> None:
    """
    Tâche planifiée à wishes_open_date. Passe recommendation → candidature
    (ouverture de la période de saisie des vœux).
    Si l'année n'est pas en RECOMMENDATION, la transition est annulée et une alerte est créée.
    """
    today = date.today()
    already_past = [
        AcademicYear.CampaignStatus.CANDIDATURE,
        AcademicYear.CampaignStatus.IMPORT,
        AcademicYear.CampaignStatus.PRE_ASSIGNMENT,
        AcademicYear.CampaignStatus.VALIDATION,
        AcademicYear.CampaignStatus.PUBLISHED,
        AcademicYear.CampaignStatus.CLOSED,
    ]
    qs = AcademicYear.objects.filter(wishes_open_date__lte=today).exclude(
        status__in=already_past
    )
    for year in qs:
        if year.status != AcademicYear.CampaignStatus.RECOMMENDATION:
            logger.warning(
                "AcademicYear %s (%s) état inattendu '%s' — transition recommendation → candidature annulée",
                year.pk,
                year.label,
                year.status,
            )
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — état inattendu « {year.status} », transition recommendation → candidature annulée.",
            )
            _alert_transition_failed(year, "recommendation", "candidature")
            continue
        try:
            year.start_candidature()
            year.save(update_fields=["status", "updated_at"])
            logger.info(
                "AcademicYear %s (%s) advanced: recommendation → candidature",
                year.pk,
                year.label,
            )
        except TransitionNotAllowed:
            logger.warning(
                "AcademicYear %s (%s) transition recommendation → candidature refused",
                year.pk,
                year.label,
            )
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — transition recommendation → candidature refusée.",
            )
            _alert_transition_failed(year, "recommendation", "candidature")


def auto_close_wishes() -> None:
    """
    Tâche planifiée à wishes_close_date. Passe candidature → import
    (clôture de la période de saisie des vœux).
    L'admin devra ensuite importer les vœux manquants et lancer manuellement l'algorithme.
    """
    today = date.today()
    already_past = [
        AcademicYear.CampaignStatus.IMPORT,
        AcademicYear.CampaignStatus.PRE_ASSIGNMENT,
        AcademicYear.CampaignStatus.VALIDATION,
        AcademicYear.CampaignStatus.PUBLISHED,
        AcademicYear.CampaignStatus.CLOSED,
    ]
    qs = AcademicYear.objects.filter(wishes_close_date__lte=today).exclude(
        status__in=already_past
    )
    for year in qs:
        if year.status != AcademicYear.CampaignStatus.CANDIDATURE:
            logger.warning(
                "AcademicYear %s (%s) état inattendu '%s' — transition candidature → import annulée",
                year.pk,
                year.label,
                year.status,
            )
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — état inattendu « {year.status} », transition candidature → import annulée.",
            )
            _alert_transition_failed(year, "candidature", "import")
            continue
        try:
            year.close_wishes()
            year.save(update_fields=["status", "updated_at"])
            logger.info(
                "AcademicYear %s (%s) advanced: candidature → import",
                year.pk,
                year.label,
            )
        except TransitionNotAllowed:
            logger.warning(
                "AcademicYear %s (%s) transition candidature → import refused",
                year.pk,
                year.label,
            )
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — transition candidature → import refusée.",
            )
            _alert_transition_failed(year, "candidature", "import")


def auto_close_academic_year() -> None:
    """
    Tâche planifiée à end_date. Clôture les années en état PUBLISHED.
    Si l'année n'est pas en PUBLISHED, une alerte est créée sans tenter la transition.
    """
    today = date.today()
    qs = AcademicYear.objects.exclude(status=AcademicYear.CampaignStatus.CLOSED).filter(
        end_date__lte=today
    )
    for year in qs:
        if year.status != AcademicYear.CampaignStatus.PUBLISHED:
            logger.warning(
                "AcademicYear %s (%s) état inattendu '%s' — transition published → closed annulée",
                year.pk,
                year.label,
                year.status,
            )
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — état inattendu « {year.status} », transition published → closed annulée.",
            )
            _alert_transition_failed_close(year)
            continue
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
                "AcademicYear %s (%s) transition published → closed refused",
                year.pk,
                year.label,
            )
            log_action(
                action="auto_transition_failed",
                detail=f"Année {year.label} ({year.pk}) — transition published → closed refusée.",
            )
            _alert_transition_failed_close(year)
