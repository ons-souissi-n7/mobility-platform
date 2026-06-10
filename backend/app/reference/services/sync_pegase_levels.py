from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from app.imports.models import (
    ImportReport,
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.integrations.pegase import PegaseClient
from app.reference.models import Level
from app.shared.sync import SyncResult, mark_raw_import


def sync_pegase_levels(
    client: PegaseClient | None = None,
    triggered_by: str = "",
) -> SyncResult:
    client = client or PegaseClient()
    result = SyncResult()

    report = ImportReport.objects.create(
        source=ImportSource.PEGASE,
        triggered_by=triggered_by,
    )

    for level in client.fetch_levels():
        result.total += 1
        payload = level.payload
        raw_import = _create_raw_import(payload, import_report=report)

        try:
            _validate_level_payload(payload)
            created = _upsert_level(payload)
        except (IntegrityError, DjangoValidationError, ValueError, KeyError) as exc:
            result.failed += 1
            mark_raw_import(raw_import, RawImportStatus.FAILED, str(exc))
            report.record_error(raw_import.external_id, str(exc), raw_import.id)
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1

        mark_raw_import(raw_import, RawImportStatus.IMPORTED)
        report.record_success()

    report.finalize()
    return result


def _validate_level_payload(payload: dict[str, Any]) -> None:
    if not payload.get("pegase_id"):
        raise ValueError("Identifiant Pégase manquant — champ obligatoire.")
    if not payload.get("code"):
        raise ValueError("Code du niveau manquant — champ obligatoire.")
    if not payload.get("name"):
        raise ValueError("Nom du niveau manquant — champ obligatoire.")


@transaction.atomic
def _upsert_level(payload: dict[str, Any]) -> bool:
    pegase_id = str(payload["pegase_id"])
    _, created = Level.objects.update_or_create(
        pegase_id=pegase_id,
        defaults={
            "code": str(payload["code"]).strip().upper(),
            "name": str(payload["name"]).strip(),
            "last_sync_pegase": timezone.now(),
        },
    )
    return created


def _create_raw_import(
    payload: dict[str, Any],
    import_report: ImportReport | None = None,
) -> RawImport:
    return RawImport.objects.create(
        source="pegase_levels",
        source_file="levels.json",
        external_id=str(payload.get("pegase_id") or ""),
        payload=payload,
        entity=RawImportEntity.LEVEL,
        import_report=import_report,
    )
