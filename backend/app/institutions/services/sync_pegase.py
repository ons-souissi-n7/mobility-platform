from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from app.reference.models import (
    Department,
    DepartmentRawImport,
    DepartmentRawImportStatus,
)
from app.shared.sync import SyncResult
from app.shared.validators import ValidationError as PegaseValidationError

from .pegase_client import PegaseClient
from .pegase_transformer import TransformedDepartment, transform_department
from .pegase_validator import validate_department


def sync_pegase_departments(client: PegaseClient | None = None) -> SyncResult:
    client = client or PegaseClient()
    result = SyncResult()

    for department in client.fetch_departments():
        result.total += 1
        payload = department.payload
        raw_import = _create_raw_import(payload)

        try:
            transformed = transform_department(payload)
            validate_department(transformed)
            created = _upsert_department(transformed)
        except (
            IntegrityError,
            DjangoValidationError,
            PegaseValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            _mark_raw_import(raw_import, DepartmentRawImportStatus.FAILED, str(exc))
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1
        _mark_raw_import(raw_import, DepartmentRawImportStatus.IMPORTED)

    return result


def _create_raw_import(payload: dict[str, Any]) -> DepartmentRawImport:
    return DepartmentRawImport.objects.create(
        source="pegase_departments",
        source_file="pegase_api",
        external_id=str(payload.get("pegase_id") or ""),
        payload=payload,
    )


def _mark_raw_import(
    raw_import: DepartmentRawImport,
    status: DepartmentRawImportStatus,
    error_message: str = "",
) -> None:
    raw_import.status = status
    raw_import.error_message = error_message
    raw_import.imported_at = (
        timezone.now() if status == DepartmentRawImportStatus.IMPORTED else None
    )
    raw_import.save(
        update_fields=["status", "error_message", "imported_at", "updated_at"]
    )


@transaction.atomic
def _upsert_department(data: TransformedDepartment) -> bool:
    department, created = Department.objects.update_or_create(
        pegase_id=data.pegase_id,
        defaults={
            "code": data.code,
            "name": data.name,
            "last_sync_pegase": timezone.now(),
        },
    )
    department.full_clean()
    return created
