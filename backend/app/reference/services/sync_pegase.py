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
from app.reference.models import Department
from app.shared.sync import (
    SyncConflictError,
    SyncResult,
    already_up_to_date,
    detect_sync_conflict,
    mark_raw_import,
)
from app.shared.validators import DomainValidationError

from .pegase_transformer import transform_department
from .pegase_validator import validate_department


def sync_pegase_departments(
    client: PegaseClient | None = None,
    triggered_by: str = "",
) -> SyncResult:
    client = client or PegaseClient()
    result = SyncResult()

    report = ImportReport.objects.create(
        source=ImportSource.PEGASE,
        triggered_by=triggered_by,
    )

    for department in client.fetch_departments():
        result.total += 1
        payload = department.payload
        raw_import = _create_raw_import(payload, import_report=report)

        try:
            transformed = transform_department(payload)
            validate_department(transformed)
            created = upsert_department(transformed)
        except SyncConflictError as exc:
            result.conflicted += 1
            mark_raw_import(raw_import, RawImportStatus.CONFLICT, str(exc))
            report.record_conflict(raw_import.external_id, str(exc), raw_import.id)
            continue
        except (
            IntegrityError,
            DjangoValidationError,
            DomainValidationError,
            ValueError,
            KeyError,
        ) as exc:
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


def _create_raw_import(
    payload: dict[str, Any],
    import_report: ImportReport | None = None,
) -> RawImport:
    return RawImport.objects.create(
        source="pegase_departments",
        source_file="fake_departments.json",
        external_id=str(payload.get("pegase_id") or ""),
        payload=payload,
        entity=RawImportEntity.DEPARTMENT,
        import_report=import_report,
    )


@transaction.atomic
def upsert_department(transformed_data: Any, force_overwrite: bool = False) -> bool:
    if isinstance(transformed_data, dict):
        transformed_data = transform_department(transformed_data)
        validate_department(transformed_data)

    # Résolution : pegase_id → code (département créé manuellement sans pegase_id)
    # Quand trouvé par code, on renseigne le pegase_id pour accélérer les recherches futures.
    department = Department.objects.filter(pegase_id=transformed_data.pegase_id).first()

    if department is None:
        department = Department.objects.filter(
            code__iexact=transformed_data.code
        ).first()

    created = department is None
    if created:
        department = Department(code=transformed_data.code)
    elif not force_overwrite:
        if already_up_to_date(
            department,
            "last_sync_pegase",
            transformed_data.source_updated_at,
            code=transformed_data.code,
            name=transformed_data.name,
        ):
            return False
        if conflict := detect_sync_conflict(
            department, "last_sync_pegase", transformed_data.source_updated_at
        ):
            raise conflict

    department.pegase_id = transformed_data.pegase_id
    department.code = transformed_data.code
    department.name = transformed_data.name
    department.full_clean()
    department.save()
    department.last_sync_pegase = department.updated_at
    department.save(update_fields=["last_sync_pegase"])
    return created
