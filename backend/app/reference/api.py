from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from ninja import Router
from ninja.errors import HttpError

from .models import Country, Department
from .schemas import CountryIn, CountryOut, DepartmentIn, DepartmentOut

router = Router()


def save_validated(instance):
    try:
        instance.full_clean()
        instance.save()
    except (IntegrityError, ValidationError) as exc:
        raise HttpError(400, str(exc)) from exc

    return instance


@router.get("/countries/", response=list[CountryOut], summary="Liste des pays")
def list_countries(request):
    return Country.objects.all()


@router.post("/countries/", response={201: CountryOut}, summary="Creer un pays")
def create_country(request, payload: CountryIn):
    country = Country(**payload.model_dump())
    return 201, save_validated(country)


@router.put(
    "/countries/{country_id}/",
    response=CountryOut,
    summary="Modifier un pays",
)
def update_country(request, country_id: int, payload: CountryIn):
    try:
        country = Country.objects.get(pk=country_id)
    except Country.DoesNotExist as exc:
        raise HttpError(404, "Pays introuvable.") from exc

    for field, value in payload.model_dump().items():
        setattr(country, field, value)

    return save_validated(country)


@router.delete(
    "/countries/{country_id}/",
    response={204: None},
    summary="Supprimer un pays",
)
def delete_country(request, country_id: int):
    try:
        country = Country.objects.get(pk=country_id)
        country.delete()
    except Country.DoesNotExist as exc:
        raise HttpError(404, "Pays introuvable.") from exc
    except ProtectedError as exc:
        raise HttpError(400, "Ce pays est utilise par une autre entite.") from exc

    return 204, None


@router.get(
    "/departments/",
    response=list[DepartmentOut],
    summary="Liste des departements",
)
def list_departments(request):
    return Department.objects.all()


@router.post(
    "/departments/",
    response={201: DepartmentOut},
    summary="Creer un departement",
)
def create_department(request, payload: DepartmentIn):
    department = Department(**payload.model_dump())
    return 201, save_validated(department)


@router.put(
    "/departments/{department_id}/",
    response=DepartmentOut,
    summary="Modifier un departement",
)
def update_department(request, department_id: int, payload: DepartmentIn):
    try:
        department = Department.objects.get(pk=department_id)
    except Department.DoesNotExist as exc:
        raise HttpError(404, "Departement introuvable.") from exc

    for field, value in payload.model_dump().items():
        setattr(department, field, value)

    return save_validated(department)


@router.delete(
    "/departments/{department_id}/",
    response={204: None},
    summary="Supprimer un departement",
)
def delete_department(request, department_id: int):
    try:
        department = Department.objects.get(pk=department_id)
        department.delete()
    except Department.DoesNotExist as exc:
        raise HttpError(404, "Departement introuvable.") from exc
    except ProtectedError as exc:
        raise HttpError(
            400, "Ce departement est utilise par une autre entite."
        ) from exc

    return 204, None
