from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from app.reference.models import (
    Department,
    DepartmentRawImport,
    DepartmentRawImportStatus,
)

from .pegase_client import PegaseClient
from .pegase_transformer import transform_department
from .pegase_validator import ValidationError as PegaseValidationError
from .pegase_validator import validate_department


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    failed: int = 0
    ignored: int = 0
    total: int = 0


def sync_pegase_departments(client: PegaseClient | None = None) -> SyncResult:
    """
    Synchronise les départements depuis l'API Pegase.
    
    Orchestre le pipeline :
    1. fetch via client
    2. transform les données brutes
    3. validate les données
    4. upsert en base
    5. track les résultats
    """
    client = client or PegaseClient()
    result = SyncResult()

    for department in client.fetch_departments():
        result.total += 1
        payload = department.payload
        raw_import = create_raw_import(payload)

        try:
            # Pipeline : Transform -> Validate -> Persist
            transformed = transform_department(payload)
            validate_department(transformed)
            created = upsert_department(transformed)
        except (
            IntegrityError,
            DjangoValidationError,
            PegaseValidationError,
            ValueError,
            KeyError,
        ) as exc:
            result.failed += 1
            mark_raw_import(raw_import, DepartmentRawImportStatus.FAILED, str(exc))
            continue

        if created:
            result.created += 1
        else:
            result.updated += 1

        mark_raw_import(raw_import, DepartmentRawImportStatus.IMPORTED)

    return result


def create_raw_import(payload: dict[str, Any]) -> DepartmentRawImport:
    return DepartmentRawImport.objects.create(
        source="pegase_fake_departments",
        source_file="fake_departments.json",
        external_id=str(payload.get("pegase_id") or ""),
        payload=payload,
    )


def mark_raw_import(
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
def upsert_department(transformed_data: Any) -> bool:
    """
    Persiste le département transformé et validé en base.
    
    Args:
        transformed_data: TransformedDepartment avec données normalisées
    
    Returns:
        True si créé, False si mis à jour
    """
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
