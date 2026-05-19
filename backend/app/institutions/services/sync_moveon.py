from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from app.institutions.models import (
    PartnerUniversity,
    PartnerUniversityRawImport,
    PartnerUniversityRawImportStatus,
)

from .moveon_client import MoveOnClient
from .moveon_country import resolve_country
from .moveon_transformer import TransformedInstitution, transform_institution
from .moveon_validator import ValidationError as MoveOnValidationError
from .moveon_validator import validate_institution



@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    ignored: int = 0
    total: int = 0


def sync_moveon_institutions(client: MoveOnClient | None = None) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    for institution in client.fetch_institutions():
        result.total += 1
        payload = institution.payload
        raw_import = create_raw_import(payload)

        try:
            transformed = transform_institution(payload)
            validate_institution(transformed)
            created = upsert_partner_university(transformed)
        except (
            IntegrityError,
            ValidationError,
            MoveOnValidationError,
            ValueError,
        ) as exc:
            result.failed += 1
            mark_raw_import(
                raw_import,
                PartnerUniversityRawImportStatus.FAILED,
                str(exc),
            )
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1

        mark_raw_import(raw_import, PartnerUniversityRawImportStatus.IMPORTED)

    return result


def create_raw_import(payload: dict[str, Any]) -> PartnerUniversityRawImport:
    return PartnerUniversityRawImport.objects.create(
        source="moveon_institutions",
        source_file="",
        external_id=str(payload.get("moveon_id") or ""),
        payload=payload,
    )


def mark_raw_import(
    raw_import: PartnerUniversityRawImport,
    status: PartnerUniversityRawImportStatus,
    error_message: str = "",
) -> None:
    raw_import.status = status
    raw_import.error_message = error_message
    raw_import.imported_at = (
        timezone.now() if status == PartnerUniversityRawImportStatus.IMPORTED else None
    )
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )


@transaction.atomic
def upsert_partner_university(transformed_data: TransformedInstitution) -> bool:
    moveon_id = transformed_data.moveon_id
    if moveon_id in (None, ""):
        raise ValueError("Missing moveon_id")

    country = resolve_country(transformed_data.country_payload)
    defaults = {
        "name": transformed_data.name,
        "short_name": transformed_data.short_name,
        "translated_name": transformed_data.translated_name,
        "erasmus_code": transformed_data.erasmus_code,
        "city": transformed_data.city,
        "url": transformed_data.url,
        "email": transformed_data.email,
        "country": country,
        "last_sync_moveon": timezone.now(),
    }

    university, created = PartnerUniversity.objects.update_or_create(
        moveon_id=moveon_id,
        defaults=defaults,
    )
    university.full_clean()
    university.save()
    return created
