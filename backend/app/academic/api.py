from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django_fsm import TransitionNotAllowed
from ninja import Router
from ninja.errors import HttpError

from app.audit.logger import log_action
from app.auth.authentication import AdminJWTAuth
from app.mobility.models import AgreementYear
from app.mobility.services.quota_estimator import (
    initialize_new_year_mobility,
    redistribute_department_quotas,
)
from app.outgoing.tasks import enqueue_gale_shapley
from app.shared.api_helpers import SelectOption, save_validated
from app.students.models import AnnualEnrollment

from .models import AcademicYear
from .schemas import AcademicYearIn, AcademicYearOut

router = Router()


def get_academic_year(year_id: int) -> AcademicYear:
    try:
        return AcademicYear.objects.get(pk=year_id)
    except AcademicYear.DoesNotExist as exc:
        raise HttpError(404, "Academic year introuvable.") from exc


@router.get(
    "/years/",
    response=list[AcademicYearOut],
    summary="Liste des annees",
    auth=AdminJWTAuth(),
)
def list_academic_years(request):
    return AcademicYear.objects.all()


@router.get(
    "/years/select-options/",
    response=list[SelectOption],
    summary="Options annees universitaires pour dropdown",
)
def list_academic_years_select(request):
    return [
        SelectOption(id=y.id, label=y.label)
        for y in AcademicYear.objects.order_by("-start_date")
    ]


@router.get(
    "/years/current/",
    response=AcademicYearOut | None,
    summary="Annee universitaire courante",
)
def get_current_academic_year(request):
    return AcademicYear.get_current()


@router.get(
    "/years/{year_id}/",
    response=AcademicYearOut,
    summary="Détail d'une année universitaire",
)
def get_academic_year_detail(request, year_id: int):
    return get_academic_year(year_id)


@router.post(
    "/years/",
    response={201: AcademicYearOut},
    summary="Creer une annee",
    auth=AdminJWTAuth(),
)
def create_academic_year(request, payload: AcademicYearIn):
    academic_year = AcademicYear(**payload.model_dump())
    saved = save_validated(academic_year)
    initialize_new_year_mobility(saved)
    return 201, saved


@router.put(
    "/years/{year_id}/",
    response=AcademicYearOut,
    summary="Modifier une annee",
    auth=AdminJWTAuth(),
)
def update_academic_year(request, year_id: int, payload: AcademicYearIn):
    academic_year = get_academic_year(year_id)

    # Champs structurels immuables dès que la campagne est lancée
    if academic_year.status != AcademicYear.CampaignStatus.INITIALIZATION:
        if payload.label != academic_year.label:
            raise HttpError(
                400, "Le libellé ne peut plus être modifié une fois la campagne lancée."
            )
        if (
            payload.start_date != academic_year.start_date
            or payload.end_date != academic_year.end_date
        ):
            raise HttpError(
                400,
                "Les dates de début et de fin ne peuvent plus être modifiées une fois la campagne lancée.",
            )

    # Dates de vœux immuables dès l'ouverture de la période de candidature
    locked_statuses = {
        AcademicYear.CampaignStatus.CANDIDATURE,
        AcademicYear.CampaignStatus.IMPORT,
        AcademicYear.CampaignStatus.PRE_ASSIGNMENT,
        AcademicYear.CampaignStatus.VALIDATION,
        AcademicYear.CampaignStatus.PUBLISHED,
        AcademicYear.CampaignStatus.FINALIZATION,
    }
    if academic_year.status in locked_statuses and (
        payload.wishes_open_date != academic_year.wishes_open_date
        or payload.wishes_close_date != academic_year.wishes_close_date
    ):
        raise HttpError(
            400,
            "Les dates d'ouverture et de clôture des vœux ne peuvent plus être modifiées "
            "une fois la période de candidature démarrée.",
        )

    for field, value in payload.model_dump().items():
        setattr(academic_year, field, value)
    return save_validated(academic_year)


@router.delete(
    "/years/{year_id}/",
    response={204: None},
    summary="Supprimer une annee",
    auth=AdminJWTAuth(),
)
def delete_academic_year(request, year_id: int):
    academic_year = get_academic_year(year_id)
    try:
        academic_year.delete()
    except ProtectedError as exc:
        raise HttpError(
            409,
            "Impossible de supprimer cette annee universitaire : "
            "des donnees y sont rattachees (quotas, accords, inscriptions...).",
        ) from exc
    return 204, None


@router.post(
    "/years/{year_id}/open-recommendation/",
    response=AcademicYearOut,
    summary="Ouvrir la phase de recommandation",
    auth=AdminJWTAuth(),
)
def open_recommendation(request, year_id: int):
    academic_year = get_academic_year(year_id)

    if not academic_year.wishes_open_date or not academic_year.wishes_close_date:
        raise HttpError(
            400,
            "Les dates d'ouverture et de clôture des vœux sont obligatoires"
            " avant de lancer la phase de recommandation.",
        )
    has_gpa = AnnualEnrollment.objects.filter(
        academic_year=academic_year, gpa__isnull=False
    ).exists()
    if not has_gpa:
        raise HttpError(
            400,
            "Aucune note GPA importée pour cette année. Importez les GPAs"
            " avant de lancer la phase de recommandation.",
        )
    has_quotas = AgreementYear.objects.filter(
        academic_year=academic_year,
        is_active=True,
        department_quotas__isnull=False,
    ).exists()
    if not has_quotas:
        raise HttpError(
            400,
            "Aucun quota de département configuré pour les accords actifs"
            " de cette année universitaire.",
        )
    result = apply_transition(academic_year, "open_recommendation")
    _auto_validate_agreement_years(academic_year)
    return result


@router.post(
    "/years/{year_id}/start-candidature/",
    response=AcademicYearOut,
    summary="Démarrer la phase de candidature (ouverture des vœux)",
    auth=AdminJWTAuth(),
)
def start_candidature(request, year_id: int):
    academic_year = get_academic_year(year_id)
    return apply_transition(academic_year, "start_candidature")


@router.post(
    "/years/{year_id}/close-wishes/",
    response=AcademicYearOut,
    summary="Clôturer les vœux (candidature → import)",
    auth=AdminJWTAuth(),
)
def close_wishes(request, year_id: int):
    academic_year = get_academic_year(year_id)
    return apply_transition(academic_year, "close_wishes")


@router.post(
    "/years/{year_id}/finalize-cti/",
    response=AcademicYearOut,
    summary="Finaliser les statistiques CTI (published → finalization)",
    auth=AdminJWTAuth(),
)
def finalize_cti(request, year_id: int):
    from app.cti.tasks import enqueue_refresh_cti_durations

    academic_year = get_academic_year(year_id)
    result = apply_transition(academic_year, "finalize_cti")

    triggered_by = getattr(request.user, "username", "")
    enqueue_refresh_cti_durations(year_id, triggered_by=triggered_by)

    log_action(
        request,
        action="finalize_cti",
        detail=(
            f"Année {academic_year.label} — finalisation CTI lancée, "
            f"calcul des durées de mobilité en cours (tâche asynchrone)."
        ),
    )
    return result


@router.post(
    "/years/{year_id}/close/",
    response=AcademicYearOut,
    summary="Clôturer l'année universitaire (finalization → closed)",
    auth=AdminJWTAuth(),
)
def close_year(request, year_id: int):
    academic_year = get_academic_year(year_id)
    result = apply_transition(academic_year, "close")
    log_action(
        request,
        action="close_year",
        detail=f"Année {academic_year.label} — clôturée manuellement.",
    )
    return result


@router.post(
    "/years/{year_id}/launch-assignment/",
    response={202: AcademicYearOut},
    summary="Lancer l'affectation (import → pre_assignment + Gale-Shapley)",
    auth=AdminJWTAuth(),
)
def launch_assignment(request, year_id: int):
    from app.students.models import StudentWish

    academic_year = get_academic_year(year_id)
    try:
        academic_year.launch_assignment()
        academic_year.save(update_fields=["status", "updated_at"])
    except TransitionNotAllowed as exc:
        raise HttpError(
            409,
            f"Impossible de lancer l'affectation depuis l'état « {academic_year.status} »."
            " L'année doit être en phase Import.",
        ) from exc

    wish_count = StudentWish.objects.filter(
        annual_enrollment__academic_year=academic_year
    ).count()
    if wish_count == 0:
        from app.alerts.models import SystemAlert

        SystemAlert.objects.create(
            level="warning",
            title=f"Affectation lancée sans vœux — {academic_year.label}",
            message=(
                f"L'algorithme Gale-Shapley a été lancé pour {academic_year.label} "
                f"mais aucun vœu étudiant n'a été enregistré. "
                f"Tous les étudiants seront marqués « non affectés »."
            ),
            academic_year=academic_year,
        )

    triggered_by = getattr(request.user, "username", "")
    enqueue_gale_shapley(year_id, triggered_by=triggered_by)
    log_action(
        request,
        action="launch_assignment",
        detail=f"Année {academic_year.label} — algorithme d'affectation lancé par {triggered_by or 'système'} ({wish_count} vœux).",
    )
    return 202, academic_year


@router.post(
    "/years/{year_id}/publish-results/",
    response=AcademicYearOut,
    summary="Publier les résultats (validation → published)",
    auth=AdminJWTAuth(),
)
def publish_results(request, year_id: int):
    from app.outgoing.models import Assignment, AssignmentStatus

    academic_year = get_academic_year(year_id)
    try:
        academic_year.publish_results()
        academic_year.save(update_fields=["status", "updated_at"])
    except TransitionNotAllowed as exc:
        raise HttpError(
            409,
            f"Impossible de publier les résultats depuis l'état « {academic_year.status} »."
            " L'année doit être en phase Validation.",
        ) from exc

    # Publier aussi l'affectation associée (proposed → validated → published si besoin)
    latest_assignment = (
        Assignment.objects.filter(academic_year=academic_year)
        .order_by("-created_at")
        .first()
    )
    if latest_assignment and latest_assignment.status in (
        AssignmentStatus.PROPOSED,
        AssignmentStatus.VALIDATED,
    ):
        try:
            if latest_assignment.status == AssignmentStatus.PROPOSED:
                latest_assignment.validate()
                latest_assignment.save(update_fields=["status", "updated_at"])
            latest_assignment.publish()
            latest_assignment.save(update_fields=["status", "updated_at"])
        except TransitionNotAllowed:
            pass  # L'affectation est déjà publiée ou dans un état incompatible

    log_action(
        request,
        action="publish_results",
        detail=f"Année {academic_year.label} — résultats publiés.",
    )
    return academic_year


def _auto_validate_agreement_years(academic_year: AcademicYear) -> None:
    now = timezone.now()
    for ay in AgreementYear.objects.filter(
        academic_year=academic_year, is_active=True, is_validated=False
    ).prefetch_related("department_quotas"):
        depts = list(ay.department_quotas.all())
        dept_total = sum(dq.get_effective_quota() for dq in depts)
        if depts and dept_total != ay.n7_places:
            redistribute_department_quotas(ay)
        ay.is_validated = True
        ay.validated_by = "Système"
        ay.validated_at = now
        ay.save(
            update_fields=["is_validated", "validated_by", "validated_at", "updated_at"]
        )


@router.post(
    "/years/{year_id}/complete-assignment/",
    response=AcademicYearOut,
    summary="Forcer la transition pre_assignment → validation (récupération après incident)",
    auth=AdminJWTAuth(),
)
def complete_assignment_recovery(request, year_id: int):
    academic_year = get_academic_year(year_id)
    if academic_year.status != AcademicYear.CampaignStatus.PRE_ASSIGNMENT:
        raise HttpError(
            409,
            f"Cette action n'est disponible que pour les années en phase Pré-affectation "
            f"(état actuel : « {academic_year.status} »).",
        )
    result = apply_transition(academic_year, "complete_assignment")
    log_action(
        request,
        action="complete_assignment_recovery",
        detail=f"Année {academic_year.label} — transition pré-affectation → validation forcée manuellement.",
    )
    return result


def apply_transition(academic_year: AcademicYear, transition_name: str) -> AcademicYear:
    try:
        getattr(academic_year, transition_name)()
    except TransitionNotAllowed as exc:
        # 409 Conflict : l'état actuel de la ressource empêche l'opération demandée
        # (cohérent avec launch_assignment/publish_results ci-dessus).
        raise HttpError(
            409,
            f"Transition « {transition_name} » non autorisée depuis l'état « {academic_year.status} ».",
        ) from exc
    academic_year.save(update_fields=["status", "updated_at"])
    return academic_year
