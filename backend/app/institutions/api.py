from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from app.reference.models import Country
from app.shared.api_helpers import save_validated

from .models import (
    PartnerUniversity,
    PartnerUniversityRawImport,
    PartnerUniversityRawImportStatus,
)
from .schemas import (
    PartnerUniversityImportOut,
    PartnerUniversityImportRetryIn,
    PartnerUniversityIn,
    PartnerUniversityOut,
)
from .services.moveon_transformer import transform_institution
from .services.moveon_validator import (
    ValidationError as MoveOnValidationError,
)
from .services.moveon_validator import (
    validate_institution,
)
from .services.sync_moveon import upsert_partner_university
from .tasks import enqueue_sync_moveon_institutions

router = Router()


@router.get(
    "/universities/",
    response=list[PartnerUniversityOut],
    summary="Liste des universites partenaires",
)
def list_universities(request):
    return PartnerUniversity.objects.select_related("country").all()


@router.post(
    "/universities/",
    response={201: PartnerUniversityOut},
    summary="Creer une universite partenaire",
)
def create_university(request, payload: PartnerUniversityIn):
    university = PartnerUniversity(**payload.model_dump())
    return 201, save_validated(university)


@router.put(
    "/universities/{university_id}/",
    response=PartnerUniversityOut,
    summary="Modifier une universite partenaire",
)
def update_university(request, university_id: int, payload: PartnerUniversityIn):
    try:
        university = PartnerUniversity.objects.get(pk=university_id)
    except PartnerUniversity.DoesNotExist as exc:
        raise HttpError(404, "Universite partenaire introuvable.") from exc

    for field, value in payload.model_dump().items():
        setattr(university, field, value)

    return save_validated(university)


@router.delete(
    "/universities/{university_id}/",
    response={204: None},
    summary="Supprimer une universite partenaire",
)
def delete_university(request, university_id: int):
    try:
        university = PartnerUniversity.objects.get(pk=university_id)
        university.delete()
    except PartnerUniversity.DoesNotExist as exc:
        raise HttpError(404, "Universite partenaire introuvable.") from exc
    except ProtectedError as exc:
        raise HttpError(
            400,
            "Cette universite partenaire est utilisee par une autre entite.",
        ) from exc

    return 204, None


@router.get(
    "/import-errors/",
    response=list[PartnerUniversityImportOut],
    summary="Liste des erreurs d'import MoveON des universites",
)
def list_university_import_errors(request):
    raw_imports = PartnerUniversityRawImport.objects.order_by("-created_at")
    latest_by_external_id = {}

    for raw_import in raw_imports:
        key = raw_import.external_id or f"raw-{raw_import.id}"
        if key not in latest_by_external_id:
            latest_by_external_id[key] = raw_import

    return [
        raw_import
        for raw_import in latest_by_external_id.values()
        if raw_import.status == PartnerUniversityRawImportStatus.FAILED
    ]


@router.get(
    "/imports/",
    response=list[PartnerUniversityImportOut],
    summary="Liste de tous les imports MoveON (erreurs, reussis, etc.)",
)
def list_university_imports(request):
    raw_imports = PartnerUniversityRawImport.objects.order_by("-created_at")
    latest_by_external_id = {}

    for raw_import in raw_imports:
        key = raw_import.external_id or f"raw-{raw_import.id}"
        if key not in latest_by_external_id:
            latest_by_external_id[key] = raw_import

    return list(latest_by_external_id.values())


@router.put(
    "/import-errors/{raw_import_id}/retry/",
    response=PartnerUniversityImportOut,
    summary="Corriger et relancer un import MoveON d'universite",
)
def retry_university_import(
    request,
    raw_import_id: int,
    payload: PartnerUniversityImportRetryIn,
):
    raw_import = get_university_raw_import(raw_import_id)
    corrected_payload = dict(raw_import.payload)
    correction = payload.model_dump()

    if correction.get("country_id"):
        try:
            country = Country.objects.get(pk=correction["country_id"])
        except Country.DoesNotExist as exc:
            raise HttpError(400, "Pays de correction introuvable.") from exc

        corrected_payload["country"] = {
            **get_country_payload(corrected_payload),
            "iso2": country.iso2,
            "name_fr": country.name_fr,
            "name_en": country.name_en,
        }
    elif correction.get("country_iso2") or correction.get("country_name"):
        corrected_payload["country"] = {
            **get_country_payload(corrected_payload),
            "iso2": (correction.get("country_iso2") or "").strip().upper(),
            "name": (correction.get("country_name") or "").strip(),
        }

    try:
        transformed = transform_institution(corrected_payload)
        validate_institution(transformed)
        upsert_partner_university(transformed)
    except (
        IntegrityError,
        ValidationError,
        MoveOnValidationError,
        ValueError,
        KeyError,
    ) as exc:
        raw_import.payload = corrected_payload
        raw_import.error_message = str(exc)
        raw_import.save(update_fields=["payload", "error_message", "updated_at"])
        raise HttpError(400, str(exc)) from exc

    raw_import.payload = corrected_payload
    raw_import.status = PartnerUniversityRawImportStatus.IMPORTED
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
    "/import-errors/{raw_import_id}/ignore/",
    response=PartnerUniversityImportOut,
    summary="Marquer une erreur d'import MoveON d'universite comme traitee",
)
def ignore_university_import(request, raw_import_id: int):
    raw_import = get_university_raw_import(raw_import_id)
    raw_import.status = PartnerUniversityRawImportStatus.IGNORED
    raw_import.error_message = (
        f"{raw_import.error_message}\nTraite manuellement par l'administrateur."
    ).strip()
    raw_import.save(update_fields=["status", "error_message", "updated_at"])
    return raw_import


@router.post(
    "/sync-moveon/",
    response={202: dict},
    summary="Demander la synchronisation des universites depuis MoveON",
)
def sync_universities_from_moveon(request):
    task_id = enqueue_sync_moveon_institutions()
    return 202, {
        "task_id": task_id,
        "message": "Synchronisation MoveON demandée en arrière-plan.",
    }


def get_university_raw_import(raw_import_id: int) -> PartnerUniversityRawImport:
    try:
        return PartnerUniversityRawImport.objects.get(
            pk=raw_import_id,
            status=PartnerUniversityRawImportStatus.FAILED,
        )
    except PartnerUniversityRawImport.DoesNotExist as exc:
        raise HttpError(404, "Erreur d'import universite introuvable.") from exc


def get_country_payload(payload: dict) -> dict:
    country = payload.get("country")
    return country if isinstance(country, dict) else {}
