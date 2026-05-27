"""
Pipeline ETL pour l'import d'accords depuis un fichier Excel.

Pour chaque ligne valide :
  1. Resout ou cree l'universite partenaire
  2. Cree ou met a jour l'accord
  3. Synchronise les contraintes departement
  4. Synchronise les contraintes niveau
  5. Cree le quota pour l'annee en cours (estimation N7 si multi-etablissements)
  6. Distribue automatiquement le quota par departement

Les erreurs ligne par ligne sont enregistrees dans RawImport.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import (
    Agreement,
    AgreementDepartmentConstraint,
    AgreementLevelConstraint,
    AgreementQuota,
    DepartmentQuota,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.reference.models import Department, Level

from .excel_importer import ExcelRow, parse_excel_file
from .quota_estimator import create_estimated_department_quotas


@dataclass
class ExcelSyncResult:
    total: int = 0
    created: int = 0
    updated: int = 0
    failed: int = 0
    skipped: int = 0


def sync_agreements_from_excel(
    file_bytes: bytes, source_file: str = "upload.xlsx"
) -> ExcelSyncResult:
    rows = parse_excel_file(file_bytes)
    result = ExcelSyncResult(total=len(rows))
    current_year = AcademicYear.get_current()

    for excel_row in rows:
        if not excel_row.is_valid:
            result.failed += 1
            _save_raw_import(excel_row, source_file, "; ".join(excel_row.errors))
            continue

        raw_import = _save_raw_import(excel_row, source_file)

        try:
            created = _process_row(excel_row, current_year)
            raw_import.status = RawImportStatus.IMPORTED
            raw_import.imported_at = timezone.now()
            raw_import.save(update_fields=["status", "imported_at", "updated_at"])

            if created:
                result.created += 1
            else:
                result.updated += 1

        except Exception as exc:
            result.failed += 1
            raw_import.status = RawImportStatus.FAILED
            raw_import.error_message = str(exc)
            raw_import.save(update_fields=["status", "error_message", "updated_at"])

    return result


@transaction.atomic
def _process_row(excel_row: ExcelRow, current_year: AcademicYear | None) -> bool:
    university = _resolve_or_create_university(excel_row.university_name)

    agreement, created = Agreement.objects.update_or_create(
        name=excel_row.agreement_name,
        partner_university=university,
        defaults={
            "relation_type": excel_row.framework_raw,
            "framework": excel_row.framework_raw,
            "is_active": True,
            "status": "active",
            "remarks": excel_row.remarks,
        },
    )

    if excel_row.department_codes:
        _sync_department_constraints(agreement, excel_row.department_codes)

    if excel_row.level_codes:
        _sync_level_constraints(agreement, excel_row.level_codes)

    if excel_row.places is not None and current_year:
        n7_places = (
            excel_row.n7_places if excel_row.n7_places is not None else excel_row.places
        )
        is_estimated = (
            excel_row.n7_is_included and len(excel_row.internal_institutions) > 1
        )
        estimation_basis = (
            f"Quota N7 estime: {excel_row.places} places / "
            f"{len(excel_row.internal_institutions)} etablissements INP."
            if is_estimated
            else ""
        )

        quota, quota_created = AgreementQuota.objects.update_or_create(
            agreement=agreement,
            academic_year_label=current_year.label,
            period="",
            defaults={
                "academic_year": current_year,
                "source_total_places": excel_row.places,
                "total_places": n7_places,
                "remaining_places": n7_places,
                "is_effective": True,
                "is_estimated": is_estimated,
                "estimation_basis": estimation_basis,
                "source_scope": "excel_import",
                "source_institutions": excel_row.institutions_raw,
                "remarks": excel_row.remarks,
            },
        )

        if (
            quota_created
            and not DepartmentQuota.objects.filter(agreement_quota=quota).exists()
        ):
            create_estimated_department_quotas(agreement, quota, current_year)

    return created


def _resolve_or_create_university(name: str) -> PartnerUniversity:
    existing = PartnerUniversity.objects.filter(name__iexact=name).first()
    if existing:
        return existing

    university, _ = PartnerUniversity.objects.get_or_create(
        name=name,
        defaults={
            "short_name": name[:50],
            "translated_name": name,
        },
    )
    return university


def _sync_department_constraints(agreement: Agreement, codes: list[str]) -> None:
    AgreementDepartmentConstraint.objects.filter(
        agreement=agreement,
        source="excel_import",
    ).update(is_active=False)

    for code in codes:
        department = Department.objects.filter(code=code).first()
        if not department:
            continue
        AgreementDepartmentConstraint.objects.update_or_create(
            agreement=agreement,
            department=department,
            defaults={"is_active": True, "source": "excel_import"},
        )


def _sync_level_constraints(agreement: Agreement, codes: list[str]) -> None:
    AgreementLevelConstraint.objects.filter(
        agreement=agreement,
        source="excel_import",
    ).update(is_active=False)

    for code in codes:
        level, _ = Level.objects.get_or_create(
            code=code,
            defaults={"name": code, "is_active": True},
        )
        AgreementLevelConstraint.objects.update_or_create(
            agreement=agreement,
            level=level,
            defaults={"is_active": True, "source": "excel_import"},
        )


def _save_raw_import(
    excel_row: ExcelRow,
    source_file: str,
    error_message: str = "",
) -> RawImport:
    status = RawImportStatus.FAILED if error_message else RawImportStatus.PENDING
    payload: dict[str, Any] = {
        **excel_row.raw,
        "row_number": excel_row.row_number,
    }
    return RawImport.objects.create(
        source="excel_import",
        source_file=source_file,
        external_id=f"row_{excel_row.row_number}_{excel_row.university_name[:30]}",
        payload=payload,
        entity=RawImportEntity.AGREEMENT,
        status=status,
        error_message=error_message,
    )
