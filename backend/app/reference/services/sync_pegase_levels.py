from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction

from app.imports.models import (
    ImportReport,
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.integrations.pegase import PegaseClient
from app.reference.models import Level
from app.shared.sync import (
    SyncConflictError,
    SyncResult,
    already_up_to_date,
    detect_sync_conflict,
    mark_raw_import,
)


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
        except SyncConflictError as exc:
            result.conflicted += 1
            mark_raw_import(raw_import, RawImportStatus.CONFLICT, str(exc))
            report.record_conflict(raw_import.external_id, str(exc), raw_import.id)
            continue
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
def _upsert_level(payload: dict[str, Any], force_overwrite: bool = False) -> bool:
    pegase_id = str(payload["pegase_id"])
    code = str(payload["code"]).strip().upper()
    name = str(payload["name"]).strip()

    # Résolution : pegase_id → code (niveau créé manuellement sans pegase_id)
    # Quand trouvé par code, on renseigne le pegase_id pour accélérer les recherches futures.
    level = Level.objects.filter(pegase_id=pegase_id).first()

    if level is None:
        level = Level.objects.filter(code__iexact=code).first()

    created = level is None
    if created:
        level = Level(code=code)
    elif not force_overwrite:
        source_updated_at = None
        raw_updated = payload.get("updated_at") or payload.get("date_modification")
        if raw_updated:
            from datetime import date, datetime

            s = str(raw_updated).strip()
            try:
                source_updated_at = date.fromisoformat(s[:10])
            except ValueError:
                for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
                    try:
                        source_updated_at = datetime.strptime(s, fmt).date()
                        break
                    except ValueError:
                        continue
        if already_up_to_date(
            level, "last_sync_pegase", source_updated_at, code=code, name=name
        ):
            return False
        if conflict := detect_sync_conflict(
            level, "last_sync_pegase", source_updated_at
        ):
            raise conflict

    level.pegase_id = pegase_id
    level.code = code
    level.name = name
    level.save()
    level.last_sync_pegase = level.updated_at
    level.save(update_fields=["last_sync_pegase"])
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
