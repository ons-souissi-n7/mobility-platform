from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django_fsm import TransitionNotAllowed
from ninja import Router
from ninja.errors import HttpError

from app.mobility.services.quota_estimator import initialize_new_year_mobility

from .models import AcademicYear
from .schemas import AcademicYearIn, AcademicYearOut

router = Router()


def get_academic_year(year_id: int) -> AcademicYear:
    try:
        return AcademicYear.objects.get(pk=year_id)
    except AcademicYear.DoesNotExist as exc:
        raise HttpError(404, "Academic year introuvable.") from exc


def save_validated(instance: AcademicYear) -> AcademicYear:
    try:
        instance.full_clean()
        instance.save()
    except (IntegrityError, ValidationError) as exc:
        raise HttpError(400, str(exc)) from exc

    return instance


@router.get("/years/", response=list[AcademicYearOut], summary="Liste des annees")
def list_academic_years(request):
    return AcademicYear.objects.all()


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
    academic_year.delete()
    return 204, None


@router.post(
    "/years/{year_id}/open-recommendation/",
    response=AcademicYearOut,
    summary="Ouvrir la phase de recommandation",
)
def open_recommendation(request, year_id: int):
    academic_year = get_academic_year(year_id)
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
    response=AcademicYearOut,
    summary="Lancer la pre-affectation",
)
def launch_pre_assignment(request, year_id: int):
    academic_year = get_academic_year(year_id)
    return apply_transition(academic_year, "launch_pre_assignment")


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
