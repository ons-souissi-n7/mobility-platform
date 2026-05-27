from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from .models import (
    Country,
    Department,
    DepartmentRawImport,
    DepartmentRawImportStatus,
    Level,
    LevelRawImport,
    LevelRawImportStatus,
)
from .schemas import (
    CountryIn,
    CountryOut,
    DepartmentImportOut,
    DepartmentImportRetryIn,
    DepartmentIn,
    DepartmentOut,
    LevelImportOut,
    LevelIn,
    LevelOut,
)
from .services.pegase_transformer import transform_department
from .services.sync_pegase import upsert_department
from .tasks import enqueue_sync_pegase_departments, enqueue_sync_pegase_levels

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
    "/departments/import-errors/",
    response=list[DepartmentImportOut],
    summary="Liste des erreurs d'import Pegase des departements",
)
def list_department_import_errors(request):
    raw_imports = DepartmentRawImport.objects.order_by("-created_at")
    latest_by_external_id = {}

    for raw_import in raw_imports:
        key = raw_import.external_id or f"raw-{raw_import.id}"
        if key not in latest_by_external_id:
            latest_by_external_id[key] = raw_import

    return [
        raw_import
        for raw_import in latest_by_external_id.values()
        if raw_import.status == DepartmentRawImportStatus.FAILED
    ]


@router.get(
    "/departments/imports/",
    response=list[DepartmentImportOut],
    summary="Liste de tous les imports Pegase (erreurs, reussis, etc.)",
)
def list_department_imports(request):
    raw_imports = DepartmentRawImport.objects.order_by("-created_at")
    latest_by_external_id = {}

    for raw_import in raw_imports:
        key = raw_import.external_id or f"raw-{raw_import.id}"
        if key not in latest_by_external_id:
            latest_by_external_id[key] = raw_import

    return list(latest_by_external_id.values())


@router.put(
    "/departments/import-errors/{raw_import_id}/retry/",
    response=DepartmentImportOut,
    summary="Relancer un import Pegase de departement",
)
def retry_department_import(
    request,
    raw_import_id: int,
    payload: DepartmentImportRetryIn,
):
    raw_import = get_department_raw_import(raw_import_id)
    corrected_payload = dict(raw_import.payload)
    correction = payload.model_dump()

    for field in ("code", "name", "pegase_id"):
        if correction.get(field) is not None:
            corrected_payload[field] = correction[field]

    try:
        transformed = transform_department(corrected_payload)
        upsert_department(transformed)
    except (IntegrityError, ValidationError, ValueError, KeyError) as exc:
        raw_import.payload = corrected_payload
        raw_import.error_message = str(exc)
        raw_import.save(update_fields=["payload", "error_message", "updated_at"])
        raise HttpError(400, str(exc)) from exc

    raw_import.payload = corrected_payload
    raw_import.status = DepartmentRawImportStatus.IMPORTED
    raw_import.error_message = ""
    raw_import.imported_at = timezone.now()
    raw_import.save(
        update_fields=[
            "payload",
            "status",
            "error_message",
            "imported_at",
            "updated_at",
        ]
    )
    return raw_import


@router.put(
    "/departments/import-errors/{raw_import_id}/ignore/",
    response=DepartmentImportOut,
    summary="Marquer une erreur d'import Pegase de departement comme traitee",
)
def ignore_department_import(request, raw_import_id: int):
    raw_import = get_department_raw_import(raw_import_id)
    raw_import.status = DepartmentRawImportStatus.IGNORED
    raw_import.error_message = (
        f"{raw_import.error_message}\nTraite manuellement par l'administrateur."
    ).strip()
    raw_import.save(update_fields=["status", "error_message", "updated_at"])
    return raw_import


@router.post(
    "/departments/sync-pegase/",
    response={202: dict},
    summary="Demander la synchronisation des departements depuis Pegase",
)
def sync_departments_from_pegase(request):
    task_id = enqueue_sync_pegase_departments()
    return 202, {
        "task_id": task_id,
        "message": "Synchronisation Pegase demandée en arrière-plan.",
    }


def get_department_raw_import(raw_import_id: int) -> DepartmentRawImport:
    try:
        return DepartmentRawImport.objects.get(
            pk=raw_import_id,
            status=DepartmentRawImportStatus.FAILED,
        )
    except DepartmentRawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import departement introuvable.") from exc


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


@router.get("/levels/", response=list[LevelOut], summary="Liste des niveaux")
def list_levels(request):
    return Level.objects.all()


@router.post("/levels/", response={201: LevelOut}, summary="Creer un niveau")
def create_level(request, payload: LevelIn):
    level = Level(**payload.model_dump())
    return 201, save_validated(level)


@router.post(
    "/levels/sync/",
    response={202: dict},
    summary="Synchroniser les niveaux depuis Pegase",
)
def sync_levels_from_pegase(request):
    task_id = enqueue_sync_pegase_levels()
    return 202, {
        "task_id": task_id,
        "message": "Synchronisation des niveaux depuis Pegase lancee.",
    }


@router.get(
    "/levels/import-errors/",
    response=list[LevelImportOut],
    summary="Liste des erreurs d'import Pegase des niveaux",
)
def list_level_import_errors(request):
    raw_imports = LevelRawImport.objects.order_by("-created_at")
    latest = {}
    for ri in raw_imports:
        key = ri.external_id or f"raw-{ri.id}"
        if key not in latest:
            latest[key] = ri
    return [ri for ri in latest.values() if ri.status == LevelRawImportStatus.FAILED]


@router.put(
    "/levels/import-errors/{raw_import_id}/ignore/",
    response=LevelImportOut,
    summary="Marquer une erreur d'import niveau comme traitee",
)
def ignore_level_import(request, raw_import_id: int):
    try:
        raw_import = LevelRawImport.objects.get(
            pk=raw_import_id, status=LevelRawImportStatus.FAILED
        )
    except LevelRawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import niveau introuvable.") from exc

    raw_import.status = LevelRawImportStatus.IGNORED
    raw_import.error_message = (
        f"{raw_import.error_message}\nTraite manuellement par l'administrateur."
    ).strip()
    raw_import.save(update_fields=["status", "error_message", "updated_at"])
    return raw_import


@router.put("/levels/{level_id}/", response=LevelOut, summary="Modifier un niveau")
def update_level(request, level_id: int, payload: LevelIn):
    try:
        level = Level.objects.get(pk=level_id)
    except Level.DoesNotExist as exc:
        raise HttpError(404, "Niveau introuvable.") from exc

    for field, value in payload.model_dump().items():
        setattr(level, field, value)

    return save_validated(level)


@router.delete(
    "/levels/{level_id}/", response={204: None}, summary="Supprimer un niveau"
)
def delete_level(request, level_id: int):
    try:
        level = Level.objects.get(pk=level_id)
        level.delete()
    except Level.DoesNotExist as exc:
        raise HttpError(404, "Niveau introuvable.") from exc
    except (IntegrityError, ProtectedError) as exc:
        raise HttpError(
            400,
            "Ce niveau est utilise par un ou plusieurs accords et ne peut pas etre supprime.",
        ) from exc

    return 204, None
