from typing import Any

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from app.institutions.models import (
    PartnerUniversity,
    PartnerUniversityRawImport,
    PartnerUniversityRawImportStatus,
)
from app.integrations.moveon import MoveOnClient
from app.shared.sync import (
    SyncConflictError,
    SyncResult,
    already_up_to_date,
    detect_sync_conflict,
)

from .moveon_country import resolve_country
from .moveon_transformer import TransformedInstitution, transform_institution
from .moveon_validator import DomainValidationError as MoveOnValidationError
from .moveon_validator import validate_institution


def sync_moveon_institutions(client: MoveOnClient | None = None) -> SyncResult:
    client = client or MoveOnClient()
    result = SyncResult()

    ignored_external_ids = frozenset(
        PartnerUniversityRawImport.objects.filter(
            status=PartnerUniversityRawImportStatus.IGNORED,
        ).values_list("external_id", flat=True)
    )

    for institution in client.fetch_institutions():
        result.total += 1
        payload = institution.payload
        external_id = str(payload.get("moveon_id") or "")
        if external_id in ignored_external_ids:
            result.ignored += 1
            continue
        raw_import = create_raw_import(payload)

        try:
            transformed = transform_institution(payload)
            validate_institution(transformed)
            created = upsert_partner_university(transformed)
        except SyncConflictError as exc:
            result.conflicted += 1
            moveon_id = str(payload.get("moveon_id") or "")
            if moveon_id:
                existing_u = (
                    PartnerUniversity.objects.filter(moveon_id=moveon_id)
                    .select_related("country")
                    .first()
                )
                if existing_u:
                    raw_import.payload = {
                        **raw_import.payload,
                        "_existing": {
                            "moveon_id": str(existing_u.moveon_id or ""),
                            "name": existing_u.name or "",
                            "short_name": existing_u.short_name or "",
                            "translated_name": existing_u.translated_name or "",
                            "erasmus_code": existing_u.erasmus_code or "",
                            "city": existing_u.city or "",
                            "url": existing_u.url or "",
                            "email": existing_u.email or "",
                            "country_name": existing_u.country.name_fr
                            if existing_u.country
                            else "",
                        },
                    }
                    raw_import.save(update_fields=["payload"])
            mark_raw_import(
                raw_import,
                PartnerUniversityRawImportStatus.CONFLICT,
                str(exc),
            )
            continue
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
def upsert_partner_university(
    transformed_data: TransformedInstitution | dict[str, Any],
    force_overwrite: bool = False,
) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_institution(transformed_data)
        validate_institution(transformed_data)

    moveon_id = transformed_data.moveon_id
    if moveon_id in (None, ""):
        raise ValueError("Missing moveon_id")

    country = resolve_country(transformed_data.country_payload)

    # Résolution en cascade : moveon_id → erasmus_code → nom
    # Quand trouvé sans moveon_id, on le renseigne pour accélérer les recherches futures.
    university = PartnerUniversity.objects.filter(moveon_id=moveon_id).first()

    if university is None and transformed_data.erasmus_code:
        university = (
            PartnerUniversity.objects.filter(
                erasmus_code__iexact=transformed_data.erasmus_code
            )
            .exclude(erasmus_code="")
            .first()
        )

    if university is None and transformed_data.name:
        name = transformed_data.name.strip()
        university = PartnerUniversity.objects.filter(
            Q(name__iexact=name)
            | Q(short_name__iexact=name)
            | Q(translated_name__iexact=name),
            moveon_id__isnull=True,
        ).first()

    created = university is None
    if created:
        university = PartnerUniversity(moveon_id=moveon_id)
    else:
        if not university.moveon_id:
            university.moveon_id = moveon_id
        if not force_overwrite:
            if already_up_to_date(
                university,
                "last_sync_moveon",
                transformed_data.source_updated_at,
                name=transformed_data.name,
                short_name=transformed_data.short_name,
                translated_name=transformed_data.translated_name,
                erasmus_code=transformed_data.erasmus_code,
                city=transformed_data.city,
                url=transformed_data.url,
                email=transformed_data.email,
            ):
                return False
            if conflict := detect_sync_conflict(
                university, "last_sync_moveon", transformed_data.source_updated_at
            ):
                raise conflict

    university.name = transformed_data.name
    university.short_name = transformed_data.short_name
    university.translated_name = transformed_data.translated_name
    university.erasmus_code = transformed_data.erasmus_code
    university.city = transformed_data.city
    university.url = transformed_data.url
    university.email = transformed_data.email
    university.country = country
    university.full_clean()
    university.save()
    university.last_sync_moveon = university.updated_at
    university.save(update_fields=["last_sync_moveon"])
    return created
