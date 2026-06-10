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
from app.reference.models import Department
from app.shared.sync import SyncResult, mark_raw_import
from app.shared.validators import ValidationError

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
        except (
            IntegrityError,
            DjangoValidationError,
            ValidationError,
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
def upsert_department(transformed_data: Any) -> bool:
    department, created = Department.objects.update_or_create(
        pegase_id=transformed_data.pegase_id,
        defaults={
            "code": transformed_data.code,
            "name": transformed_data.name,
            "last_sync_pegase": timezone.now(),
        },
    )
    department.full_clean()
    department.save()
    return created
