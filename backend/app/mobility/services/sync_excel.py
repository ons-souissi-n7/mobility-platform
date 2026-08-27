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
    AgreementDepartment,
    AgreementYear,
    MobilityCategory,
)
from app.reference.models import Department, Level

from .excel_importer import ExcelRow, parse_excel_file
from .quota_estimator import estimate_n7_from_inp, redistribute_department_quotas


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

    # Pré-chargement des IGNORED — évite une requête par ligne dans la boucle
    ignored_external_ids = set(
        RawImport.objects.filter(
            entity=RawImportEntity.AGREEMENT,
            status=RawImportStatus.IGNORED,
        ).values_list("external_id", flat=True)
    )

    for excel_row in rows:
        external_id = (
            f"row_{excel_row.row_number}_{(excel_row.university_name or '')[:30]}"
        )

        if external_id in ignored_external_ids:
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
            "duration_weeks": excel_row.duration_weeks,
        },
    )

    # Sync department constraints
    if excel_row.department_codes:
        depts = list(Department.objects.filter(code__in=excel_row.department_codes))
        for dept in depts:
            AgreementDepartment.objects.get_or_create(
                agreement=agreement, department=dept
            )

    if excel_row.level_codes:
        levels = []
        for code in excel_row.level_codes:
            level, _ = Level.objects.get_or_create(code=code, defaults={"name": code})
            levels.append(level)
        agreement.levels.set(levels)

    # Create AgreementYear for current year if INP quota is defined
    if current_year and inp_total > 0:
        if excel_row.n7_places is not None:
            n7 = excel_row.n7_places
        else:
            n7 = estimate_n7_from_inp(
                agreement, inp_places=inp_total, current_year=current_year
            )

        year_instance, year_created = AgreementYear.objects.get_or_create(
            agreement=agreement,
            academic_year=current_year,
            defaults={
                "is_active": True,
                "inp_total_places": inp_total,
                "n7_places": n7,
            },
        )

        if year_created:
            redistribute_department_quotas(year_instance)

    return created


def _resolve_or_create_university(raw_label: str) -> PartnerUniversity:
    # Essai direct (rétrocompatibilité avec les fichiers anciens)
    u = PartnerUniversity.objects.filter(name__iexact=raw_label).first()
    if u:
        return u
    u = PartnerUniversity.objects.filter(short_name__iexact=raw_label).first()
    if u:
        return u

    # Nouveau format "Nom (Sigle) — Pays" : extraire la partie université
    name_part = raw_label.split(" — ")[0].strip()
    if name_part != raw_label:
        u = PartnerUniversity.objects.filter(name__iexact=name_part).first()
        if u:
            return u
        u = PartnerUniversity.objects.filter(short_name__iexact=name_part).first()
        if u:
            return u

    # Si name_part contient " (Sigle)", tester nom de base et sigle séparément
    if name_part.endswith(")") and " (" in name_part:
        idx = name_part.rfind(" (")
        base_name = name_part[:idx].strip()
        short = name_part[idx + 2 : -1].strip()
        u = PartnerUniversity.objects.filter(name__iexact=base_name).first()
        if u:
            return u
        if short:
            u = PartnerUniversity.objects.filter(short_name__iexact=short).first()
            if u:
                return u

    raise ValueError(
        f"Université introuvable : « {raw_label} ». "
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
