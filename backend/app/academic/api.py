from django.db.models.deletion import ProtectedError
from django_fsm import TransitionNotAllowed
from ninja import Router
from ninja.errors import HttpError

from app.audit.logger import log_action
from app.mobility.models import AgreementYear
from app.mobility.services.quota_estimator import initialize_new_year_mobility
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


@router.get("/years/", response=list[AcademicYearOut], summary="Liste des annees")
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


@router.post("/years/", response={201: AcademicYearOut}, summary="Creer une annee")
def create_academic_year(request, payload: AcademicYearIn):
    academic_year = AcademicYear(**payload.model_dump())
    saved = save_validated(academic_year)
    initialize_new_year_mobility(saved)
    return 201, saved


@router.put(
    "/years/{year_id}/",
    response=AcademicYearOut,
    summary="Modifier une annee",
)
def update_academic_year(request, year_id: int, payload: AcademicYearIn):
    academic_year = get_academic_year(year_id)

    for field, value in payload.model_dump().items():
        setattr(academic_year, field, value)

    return save_validated(academic_year)


@router.delete(
    "/years/{year_id}/",
    response={204: None},
    summary="Supprimer une annee",
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

    return apply_transition(academic_year, "open_recommendation")


@router.post(
    "/years/{year_id}/start-consolidation/",
    response=AcademicYearOut,
    summary="Demarrer la consolidation",
)
def start_consolidation(request, year_id: int):
    academic_year = get_academic_year(year_id)
    return apply_transition(academic_year, "start_consolidation")


@router.post(
    "/years/{year_id}/launch-pre-assignment/",
    response={202: AcademicYearOut},
    summary="Lancer la pre-affectation",
)
def launch_pre_assignment(request, year_id: int):
    academic_year = get_academic_year(year_id)
    try:
        academic_year.launch_pre_assignment()
        academic_year.save(update_fields=["status", "updated_at"])
    except TransitionNotAllowed as exc:
        raise HttpError(
            409, f"Transition impossible depuis l'état '{academic_year.status}'."
        ) from exc
    triggered_by = getattr(request.user, "username", "")
    enqueue_gale_shapley(year_id, triggered_by=triggered_by)
    log_action(
        request,
        action="launch_pre_assignment",
        detail=f"Année {academic_year.label} — Gale-Shapley lancé par {triggered_by or 'système'}",
    )
    return 202, academic_year


@router.post(
    "/years/{year_id}/submit-for-validation/",
    response=AcademicYearOut,
    summary="Soumettre pour validation",
)
def submit_for_validation(request, year_id: int):
    academic_year = get_academic_year(year_id)
    return apply_transition(academic_year, "submit_for_validation")


@router.post(
    "/years/{year_id}/close/",
    response=AcademicYearOut,
    summary="Clote l'annee universitaire",
)
def close_academic_year(request, year_id: int):
    academic_year = get_academic_year(year_id)
    return apply_transition(academic_year, "close")


def apply_transition(academic_year: AcademicYear, transition_name: str) -> AcademicYear:
    try:
        getattr(academic_year, transition_name)()
    except TransitionNotAllowed as exc:
        raise HttpError(400, "Transition non autorisee.") from exc

    return save_validated(academic_year)
