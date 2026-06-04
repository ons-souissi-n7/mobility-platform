"""
Pipeline ETL pour l'import d'accords depuis un fichier Excel.

Pour chaque ligne valide :
  1. Résout ou crée l'université partenaire
  2. Crée ou met à jour l'accord (avec les M2M departments/levels)
  3. Si une année courante existe, crée l'AgreementYear avec estimation N7

Les erreurs ligne par ligne sont enregistrées dans ImportReport + RawImport.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from app.academic.models import AcademicYear
from app.imports.models import (
    ImportReport,
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.institutions.models import PartnerUniversity
from app.mobility.models import (
    Agreement,
    AgreementYear,
    MobilityCategory,
)
from app.reference.models import Department, Level

from .excel_importer import ExcelRow, parse_excel_file
from .quota_estimator import _create_department_quotas


@dataclass
class ExcelSyncResult:
    total: int = 0
    created: int = 0
    updated: int = 0
    failed: int = 0
    skipped: int = 0


def sync_agreements_from_excel(
    file_bytes: bytes,
    source_file: str = "upload.xlsx",
    academic_year: AcademicYear | None = None,
    triggered_by: str = "",
) -> ExcelSyncResult:
    rows = parse_excel_file(file_bytes)
    result = ExcelSyncResult(total=len(rows))

    if academic_year is None:
        academic_year = AcademicYear.get_current()

    report = ImportReport.objects.create(
        source=ImportSource.EXCEL,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    for excel_row in rows:
        external_id = (
            f"row_{excel_row.row_number}_{(excel_row.university_name or '')[:30]}"
        )

        if RawImport.objects.filter(
            external_id=external_id,
            entity=RawImportEntity.AGREEMENT,
            status=RawImportStatus.IGNORED,
        ).exists():
            result.skipped += 1
            continue

        if not excel_row.is_valid:
            result.failed += 1
            error_msg = "; ".join(excel_row.errors)
            _save_raw_import(
                excel_row,
                source_file,
                error_msg,
                import_report=report,
                academic_year=academic_year,
            )
            report.record_error(external_id, error_msg)
            continue

        raw_import = _save_raw_import(
            excel_row,
            source_file,
            import_report=report,
            academic_year=academic_year,
        )

        try:
            created = _process_row(excel_row, academic_year)
            raw_import.status = RawImportStatus.IMPORTED
            raw_import.imported_at = timezone.now()
            raw_import.save(update_fields=["status", "imported_at", "updated_at"])

            if created:
                result.created += 1
            else:
                result.updated += 1
            report.record_success()

        except Exception as exc:
            result.failed += 1
            error_msg = str(exc)
            raw_import.status = RawImportStatus.FAILED
            raw_import.error_message = error_msg
            raw_import.save(update_fields=["status", "error_message", "updated_at"])
            report.record_error(external_id, error_msg, raw_import.id)

    report.finalize()
    return result


@transaction.atomic
def _process_row(excel_row: ExcelRow, current_year: AcademicYear | None) -> bool:
    university = _resolve_or_create_university(excel_row.university_name)
    category = _resolve_category(excel_row.framework_raw)

    inp_total = excel_row.places or 0
    institutions = excel_row.institutions_raw or ""

    agreement, created = Agreement.objects.update_or_create(
        name=excel_row.agreement_name,
        partner_university=university,
        defaults={
            "category": category,
            "inp_total_places": inp_total,
            "inp_institutions": institutions,
            "remarks": excel_row.remarks,
        },
    )

    # Sync M2M constraints
    if excel_row.department_codes:
        depts = list(Department.objects.filter(code__in=excel_row.department_codes))
        agreement.departments.set(depts)

    if excel_row.level_codes:
        levels = []
        for code in excel_row.level_codes:
            level, _ = Level.objects.get_or_create(
                code=code, defaults={"name": code, "is_active": True}
            )
            levels.append(level)
        agreement.levels.set(levels)

    # Create AgreementYear for current year if INP quota is defined
    if current_year and inp_total > 0:
        institutions_list = [i.strip() for i in institutions.split(",") if i.strip()]
        n_institutions = max(1, len(institutions_list))

        if excel_row.n7_places is not None:
            n7 = excel_row.n7_places
        else:
            n7 = max(1, round(inp_total / n_institutions))

        year_instance, year_created = AgreementYear.objects.get_or_create(
            agreement=agreement,
            academic_year=current_year,
            defaults={"is_active": True, "n7_places": n7},
        )

        if year_created:
            _create_department_quotas(year_instance, previous_year=None)

    return created


def _resolve_or_create_university(name: str) -> PartnerUniversity:
    university = PartnerUniversity.objects.filter(name__iexact=name).first()
    if university:
        return university
    university = PartnerUniversity.objects.filter(short_name__iexact=name).first()
    if university:
        return university
    raise ValueError(
        f"Université introuvable : « {name} ». "
        "Ajoutez d'abord l'université dans le référentiel, puis relancez l'import."
    )


def _resolve_category(name: str) -> MobilityCategory | None:
    if not name:
        return None
    normalized = " ".join(name.strip().casefold().split())
    for c in MobilityCategory.objects.all():
        if " ".join(c.name.strip().casefold().split()) == normalized:
            return c
    return None


def _save_raw_import(
    excel_row: ExcelRow,
    source_file: str,
    error_message: str = "",
    import_report: ImportReport | None = None,
    academic_year: AcademicYear | None = None,
) -> RawImport:
    status = RawImportStatus.FAILED if error_message else RawImportStatus.PENDING
    payload: dict[str, Any] = {**excel_row.raw, "row_number": excel_row.row_number}
    return RawImport.objects.create(
        source="excel_import",
        source_file=source_file,
        external_id=f"row_{excel_row.row_number}_{(excel_row.university_name or '')[:30]}",
        payload=payload,
        entity=RawImportEntity.AGREEMENT,
        status=status,
        error_message=error_message,
        import_report=import_report,
        academic_year=academic_year,
    )
