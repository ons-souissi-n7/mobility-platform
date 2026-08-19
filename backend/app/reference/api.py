from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Max, ProtectedError
from django.utils import timezone
from ninja import Query, Router
from ninja.errors import HttpError

from app.audit.logger import log_action
from app.auth.authentication import AdminJWTAuth
from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.shared.api_helpers import (
    PagedResponse,
    PaginationQuery,
    SelectOption,
    paginate,
    save_validated,
)

from .models import Country, Department, Level, Parcours
from .schemas import (
    CountryIn,
    CountryOut,
    DepartmentImportRetryIn,
    DepartmentIn,
    DepartmentOut,
    LevelIn,
    LevelOut,
    ParcoursIn,
    ParcoursOut,
    RawImportOut,
)
from .services.pegase_transformer import transform_department
from .services.sync_pegase import upsert_department
from .tasks import enqueue_sync_pegase_departments, enqueue_sync_pegase_levels

router = Router()


@router.get("/countries/", response=list[CountryOut], summary="Liste des pays")
def list_countries(request):
    return Country.objects.all()


@router.get(
    "/countries/select-options/",
    response=list[SelectOption],
    summary="Options pays pour dropdown",
)
def list_countries_select(request):
    return [
        SelectOption(id=c.id, label=c.name_fr)
        for c in Country.objects.order_by("name_fr")
    ]


@router.post(
    "/countries/",
    response={201: CountryOut},
    summary="Creer un pays",
    auth=AdminJWTAuth(),
)
def create_country(request, payload: CountryIn):
    country = Country(**payload.model_dump())
    return 201, save_validated(country)


@router.put(
    "/countries/{country_id}/",
    response=CountryOut,
    summary="Modifier un pays",
    auth=AdminJWTAuth(),
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
    auth=AdminJWTAuth(),
)
def delete_country(request, country_id: int):
    try:
        country = Country.objects.get(pk=country_id)
        country.delete()
    except Country.DoesNotExist as exc:
        raise HttpError(404, "Pays introuvable.") from exc
    except ProtectedError as exc:
        # 409 Conflict : cohérent avec safe_delete() dans mobility/internships.
        raise HttpError(409, "Ce pays est utilise par une autre entite.") from exc

    return 204, None


@router.get(
    "/departments/import-errors/",
    response=PagedResponse[RawImportOut],
    summary="Liste des erreurs d'import Pegase des departements",
    auth=AdminJWTAuth(),
)
def list_department_import_errors(request, pagination: PaginationQuery = Query(...)):
    latest_ids = (
        RawImport.objects.filter(entity=RawImportEntity.DEPARTMENT)
        .values("external_id")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    qs = RawImport.objects.filter(
        id__in=latest_ids,
        status__in=[RawImportStatus.FAILED, RawImportStatus.CONFLICT],
    ).order_by("-created_at")
    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count, page=pagination.page, page_size=pagination.page_size, results=items
    )


@router.get(
    "/departments/imports/",
    response=list[RawImportOut],
    summary="Liste de tous les imports Pegase (erreurs, reussis, etc.)",
    auth=AdminJWTAuth(),
)
def list_department_imports(request):
    raw_imports = RawImport.objects.filter(entity=RawImportEntity.DEPARTMENT).order_by(
        "-created_at"
    )
    latest_by_external_id = {}
    for raw_import in raw_imports:
        key = raw_import.external_id or f"raw-{raw_import.id}"
        if key not in latest_by_external_id:
            latest_by_external_id[key] = raw_import
    return list(latest_by_external_id.values())


@router.put(
    "/departments/import-errors/{raw_import_id}/retry/",
    response=RawImportOut,
    summary="Relancer un import Pegase de departement",
    auth=AdminJWTAuth(),
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
    raw_import.status = RawImportStatus.IMPORTED
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
    response=RawImportOut,
    summary="Marquer une erreur d'import Pegase de departement comme traitee",
    auth=AdminJWTAuth(),
)
def ignore_department_import(request, raw_import_id: int):
    try:
        raw_import = RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.DEPARTMENT,
            status__in=[RawImportStatus.FAILED, RawImportStatus.CONFLICT],
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import departement introuvable.") from exc
    now = timezone.now()
    RawImport.objects.filter(
        source=raw_import.source,
        external_id=raw_import.external_id,
    ).exclude(status=RawImportStatus.IGNORED).update(
        status=RawImportStatus.IGNORED,
        error_message="Traite manuellement",
        updated_at=now,
    )
    raw_import.refresh_from_db()
    return raw_import


@router.post(
    "/departments/sync-pegase/",
    response={202: dict},
    summary="Demander la synchronisation des departements depuis Pegase",
    auth=AdminJWTAuth(),
)
def sync_departments_from_pegase(request):
    task_id = enqueue_sync_pegase_departments()
    log_action(
        request, action="sync_pegase_departments", detail=f"Tâche {task_id} lancée"
    )
    return 202, {
        "task_id": task_id,
        "message": "Synchronisation Pegase demandée en arrière-plan.",
    }


def get_department_raw_import(raw_import_id: int) -> RawImport:
    """Used by retry endpoint — only FAILED records can be retried (CONFLICT → force-overwrite)."""
    try:
        return RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.DEPARTMENT,
            status=RawImportStatus.FAILED,
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import departement introuvable.") from exc


@router.post(
    "/departments/import-errors/{raw_import_id}/force-overwrite/",
    response=RawImportOut,
    summary="Forcer la mise a jour d'un departement en conflit",
    auth=AdminJWTAuth(),
)
def force_overwrite_department_import(request, raw_import_id: int):
    try:
        raw_import = RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.DEPARTMENT,
            status=RawImportStatus.CONFLICT,
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Departement en conflit introuvable.") from exc

    try:
        upsert_department(raw_import.payload, force_overwrite=True)
    except (IntegrityError, ValidationError, ValueError, KeyError) as exc:
        raise HttpError(400, str(exc)) from exc

    raw_import.status = RawImportStatus.IMPORTED
    raw_import.error_message = ""
    raw_import.imported_at = timezone.now()
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )
    return raw_import


@router.get(
    "/departments/",
    response=list[DepartmentOut],
    summary="Liste des departements",
)
def list_departments(request):
    return Department.objects.all()


@router.get(
    "/departments/select-options/",
    response=list[SelectOption],
    summary="Options departements pour dropdown",
)
def list_departments_select(request):
    return [
        SelectOption(id=d.id, label=f"{d.code} – {d.name}")
        for d in Department.objects.order_by("code")
    ]


@router.post(
    "/departments/",
    response={201: DepartmentOut},
    summary="Creer un departement",
    auth=AdminJWTAuth(),
)
def create_department(request, payload: DepartmentIn):
    department = Department(**payload.model_dump())
    return 201, save_validated(department)


@router.put(
    "/departments/{department_id}/",
    response=DepartmentOut,
    summary="Modifier un departement",
    auth=AdminJWTAuth(),
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
    auth=AdminJWTAuth(),
)
def delete_department(request, department_id: int):
    try:
        department = Department.objects.get(pk=department_id)
        department.delete()
    except Department.DoesNotExist as exc:
        raise HttpError(404, "Departement introuvable.") from exc
    except ProtectedError as exc:
        raise HttpError(
            409, "Ce departement est utilise par une autre entite."
        ) from exc

    return 204, None


@router.get("/levels/", response=list[LevelOut], summary="Liste des niveaux")
def list_levels(request):
    return Level.objects.all()


@router.get(
    "/levels/select-options/",
    response=list[SelectOption],
    summary="Options niveaux pour dropdown",
)
def list_levels_select(request):
    return [
        SelectOption(id=level.id, label=f"{level.code} – {level.name}")
        for level in Level.objects.order_by("code")
    ]


@router.post(
    "/levels/", response={201: LevelOut}, summary="Creer un niveau", auth=AdminJWTAuth()
)
def create_level(request, payload: LevelIn):
    level = Level(**payload.model_dump())
    return 201, save_validated(level)


@router.post(
    "/levels/sync/",
    response={202: dict},
    summary="Synchroniser les niveaux depuis Pegase",
    auth=AdminJWTAuth(),
)
def sync_levels_from_pegase(request):
    task_id = enqueue_sync_pegase_levels()
    log_action(request, action="sync_pegase_levels", detail=f"Tâche {task_id} lancée")
    return 202, {
        "task_id": task_id,
        "message": "Synchronisation des niveaux depuis Pegase lancee.",
    }


@router.get(
    "/levels/import-errors/",
    response=PagedResponse[RawImportOut],
    summary="Liste des erreurs d'import Pegase des niveaux",
    auth=AdminJWTAuth(),
)
def list_level_import_errors(request, pagination: PaginationQuery = Query(...)):
    latest_ids = (
        RawImport.objects.filter(entity=RawImportEntity.LEVEL)
        .values("external_id")
        .annotate(latest_id=Max("id"))
        .values_list("latest_id", flat=True)
    )
    qs = RawImport.objects.filter(
        id__in=latest_ids,
        status__in=[RawImportStatus.FAILED, RawImportStatus.CONFLICT],
    ).order_by("-created_at")
    count, items = paginate(qs, pagination.page, pagination.page_size)
    return PagedResponse(
        count=count, page=pagination.page, page_size=pagination.page_size, results=items
    )


@router.post(
    "/levels/import-errors/{raw_import_id}/force-overwrite/",
    response=RawImportOut,
    summary="Forcer la mise a jour d'un niveau en conflit",
    auth=AdminJWTAuth(),
)
def force_overwrite_level_import(request, raw_import_id: int):
    try:
        raw_import = RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.LEVEL,
            status=RawImportStatus.CONFLICT,
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Niveau en conflit introuvable.") from exc

    try:
        from .services.sync_pegase_levels import upsert_level

        upsert_level(raw_import.payload, force_overwrite=True)
    except (IntegrityError, ValidationError, ValueError, KeyError) as exc:
        raise HttpError(400, str(exc)) from exc

    raw_import.status = RawImportStatus.IMPORTED
    raw_import.error_message = ""
    raw_import.imported_at = timezone.now()
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )
    return raw_import


@router.put(
    "/levels/import-errors/{raw_import_id}/ignore/",
    response=RawImportOut,
    summary="Marquer une erreur d'import niveau comme traitee",
    auth=AdminJWTAuth(),
)
def ignore_level_import(request, raw_import_id: int):
    try:
        raw_import = RawImport.objects.get(
            pk=raw_import_id,
            entity=RawImportEntity.LEVEL,
            status__in=[RawImportStatus.FAILED, RawImportStatus.CONFLICT],
        )
    except RawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import niveau introuvable.") from exc
    now = timezone.now()
    RawImport.objects.filter(
        source=raw_import.source,
        external_id=raw_import.external_id,
    ).exclude(status=RawImportStatus.IGNORED).update(
        status=RawImportStatus.IGNORED,
        error_message="Traite manuellement",
        updated_at=now,
    )
    raw_import.refresh_from_db()
    return raw_import


@router.put(
    "/levels/{level_id}/",
    response=LevelOut,
    summary="Modifier un niveau",
    auth=AdminJWTAuth(),
)
def update_level(request, level_id: int, payload: LevelIn):
    try:
        level = Level.objects.get(pk=level_id)
    except Level.DoesNotExist as exc:
        raise HttpError(404, "Niveau introuvable.") from exc

    for field, value in payload.model_dump().items():
        setattr(level, field, value)

    return save_validated(level)


@router.delete(
    "/levels/{level_id}/",
    response={204: None},
    summary="Supprimer un niveau",
    auth=AdminJWTAuth(),
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


@router.get("/parcours/", response=list[ParcoursOut], summary="Liste des parcours")
def list_parcours(request):
    department_id = request.GET.get("department_id")
    qs = Parcours.objects.select_related("department").order_by(
        "department__code", "code"
    )
    if department_id:
        qs = qs.filter(department_id=department_id)
    return qs


@router.get(
    "/parcours/select-options/",
    response=list[SelectOption],
    summary="Options parcours pour dropdown",
)
def list_parcours_select(request):
    department_id = request.GET.get("department_id")
    qs = Parcours.objects.select_related("department").order_by(
        "department__code", "code"
    )
    if department_id:
        qs = qs.filter(department_id=department_id)
    return [SelectOption(id=p.id, label=f"{p.code} – {p.label}") for p in qs]


@router.post(
    "/parcours/",
    response={201: ParcoursOut},
    summary="Creer un parcours",
    auth=AdminJWTAuth(),
)
def create_parcours(request, payload: ParcoursIn):
    parcours = Parcours(**payload.model_dump())
    return 201, save_validated(parcours)


@router.put(
    "/parcours/{parcours_id}/",
    response=ParcoursOut,
    summary="Modifier un parcours",
    auth=AdminJWTAuth(),
)
def update_parcours(request, parcours_id: int, payload: ParcoursIn):
    try:
        parcours = Parcours.objects.get(pk=parcours_id)
    except Parcours.DoesNotExist as exc:
        raise HttpError(404, "Parcours introuvable.") from exc

    for field, value in payload.model_dump().items():
        setattr(parcours, field, value)

    return save_validated(parcours)


@router.delete(
    "/parcours/{parcours_id}/",
    response={204: None},
    summary="Supprimer un parcours",
    auth=AdminJWTAuth(),
)
def delete_parcours(request, parcours_id: int):
    try:
        parcours = Parcours.objects.get(pk=parcours_id)
        parcours.delete()
    except Parcours.DoesNotExist as exc:
        raise HttpError(404, "Parcours introuvable.") from exc
    except ProtectedError as exc:
        raise HttpError(400, "Ce parcours est utilise par un etudiant.") from exc

    return 204, None
