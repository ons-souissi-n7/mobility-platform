from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from app.integrations.pegase import PegaseClient
from app.reference.models import Level, LevelRawImport, LevelRawImportStatus


@dataclass
class LevelSyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    total: int = 0


def sync_pegase_levels(client: PegaseClient | None = None) -> LevelSyncResult:
    client = client or PegaseClient()
    result = LevelSyncResult()

    for level in client.fetch_levels():
        result.total += 1
        payload = level.payload
        raw_import = _create_raw_import(payload)

        try:
            _validate_level_payload(payload)
            created = _upsert_level(payload)
        except (IntegrityError, DjangoValidationError, ValueError, KeyError) as exc:
            result.failed += 1
            _mark_raw_import(raw_import, LevelRawImportStatus.FAILED, str(exc))
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1

        _mark_raw_import(raw_import, LevelRawImportStatus.IMPORTED)

    return result


def _validate_level_payload(payload: dict[str, Any]) -> None:
    if not payload.get("pegase_id"):
        raise ValueError("pegase_id is required")
    if not payload.get("code"):
        raise ValueError("code is required")
    if not payload.get("name"):
        raise ValueError("name is required")


@transaction.atomic
def _upsert_level(payload: dict[str, Any]) -> bool:
    pegase_id = str(payload["pegase_id"])
    _, created = Level.objects.update_or_create(
        pegase_id=pegase_id,
        defaults={
            "code": str(payload["code"]).strip().upper(),
            "name": str(payload["name"]).strip(),
            "is_active": bool(payload.get("is_active", True)),
            "last_sync_pegase": timezone.now(),
        },
    )
    return created


def _create_raw_import(payload: dict[str, Any]) -> LevelRawImport:
    return LevelRawImport.objects.create(
        source="pegase_levels",
        source_file="levels.json",
        external_id=str(payload.get("pegase_id") or ""),
        payload=payload,
    )


def _mark_raw_import(
    raw_import: LevelRawImport, status: str, error_message: str = ""
) -> None:
    raw_import.status = status
    raw_import.error_message = error_message
    raw_import.imported_at = (
        timezone.now() if status == LevelRawImportStatus.IMPORTED else None
    )
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )
