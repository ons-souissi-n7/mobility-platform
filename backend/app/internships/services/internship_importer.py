from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO

from django.db import IntegrityError
from django.utils import timezone

from app.academic.models import AcademicYear
from app.imports.models import (
    ImportReport,
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.reference.models import Country
from app.students.models import Student

from ..models import Internship

logger = logging.getLogger(__name__)

_COLUMNS = [
    "Étudiant (INE – Nom Prénom)",
    "N°INE",
    "Raison sociale",
    "Pays",
    "Ville",
    "Date de début",
    "Date de fin",
    "Nb semaines",
    "Type",
    "Titre",
    "Tuteur pédagogique",
    "Tuteur entreprise",
]


def _extract_ine(raw: str) -> str:
    """Extrait l'INE depuis 'INE – Nom Prénom' ou retourne la valeur brute."""
    for sep in (" – ", " - ", "–", "-"):
        if sep in raw:
            return raw.split(sep, 1)[0].strip()
    return raw.strip()


@dataclass
class ExcelSyncResult:
    total: int = 0
    created: int = 0
    updated: int = 0
    failed: int = 0
    skipped: int = 0


def import_internships_from_excel(
    file_bytes: bytes,
    source_file: str,
    academic_year: AcademicYear,
    triggered_by: str = "",
) -> ExcelSyncResult:
    import openpyxl

    result = ExcelSyncResult()
    report = ImportReport.objects.create(
        source=ImportSource.EXCEL,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        report.finalize()
        return result

    # Find column indices from header row
    header = [str(c).strip() if c else "" for c in rows[0]]
    col_idx = {name: header.index(name) for name in _COLUMNS if name in header}

    def _get(row, name):
        idx = col_idx.get(name)
        if idx is None:
            return None
        val = row[idx] if idx < len(row) else None
        return str(val).strip() if val is not None else ""

    student_cache: dict[str, Student | None] = {}
    country_cache: dict[str, Country | None] = {}

    for row_number, row in enumerate(rows[1:], start=2):
        result.total += 1
        raw_ine = _get(row, "Étudiant (INE – Nom Prénom)") or _get(row, "N°INE") or ""
        ine = _extract_ine(raw_ine)
        company_name = _get(row, "Raison sociale") or ""
        external_id = f"row_{row_number}_{company_name[:30]}"

        if not ine or not company_name:
            result.failed += 1
            error_msg = "INE ou raison sociale manquant."
            _save_raw(
                row, col_idx, row_number, source_file, error_msg, report, academic_year
            )
            report.record_error(external_id, error_msg)
            continue

        if ine not in student_cache:
            student_cache[ine] = Student.objects.filter(ine=ine).first()
        student = student_cache[ine]

        if student is None:
            result.failed += 1
            error_msg = f"Étudiant introuvable (INE : {ine!r})."
            _save_raw(
                row, col_idx, row_number, source_file, error_msg, report, academic_year
            )
            report.record_error(external_id, error_msg)
            continue

        country_name = _get(row, "Pays") or ""
        if country_name not in country_cache:
            c = Country.objects.filter(name_fr__iexact=country_name).first()
            if c is None:
                c = Country.objects.filter(name_en__iexact=country_name).first()
            country_cache[country_name] = c
        country = country_cache.get(country_name)

        start_date = _parse_date(_get(row, "Date de début"))
        end_date = _parse_date(_get(row, "Date de fin"))
        weeks_raw = _get(row, "Nb semaines")
        weeks = None
        if weeks_raw:
            try:
                weeks = int(weeks_raw)
            except (ValueError, TypeError):
                pass

        raw = _save_raw(
            row, col_idx, row_number, source_file, "", report, academic_year
        )

        try:
            _, created = Internship.objects.update_or_create(
                student=student,
                company_name=company_name,
                start_date=start_date,
                defaults={
                    "academic_year": academic_year,
                    "country": country,
                    "city": _get(row, "Ville") or "",
                    "title": _get(row, "Titre") or "",
                    "internship_type": _get(row, "Type") or "",
                    "end_date": end_date,
                    "weeks_in_company": weeks,
                    "school_tutor": _get(row, "Tuteur pédagogique") or "",
                    "company_tutor": _get(row, "Tuteur entreprise") or "",
                },
            )
            raw.status = RawImportStatus.IMPORTED
            raw.imported_at = timezone.now()
            raw.save(update_fields=["status", "imported_at", "updated_at"])
            if created:
                result.created += 1
            else:
                result.updated += 1
            report.record_success()
        except (IntegrityError, Exception) as exc:
            result.failed += 1
            error_msg = str(exc)
            raw.status = RawImportStatus.FAILED
            raw.error_message = error_msg
            raw.save(update_fields=["status", "error_message", "updated_at"])
            report.record_error(external_id, error_msg, raw.id)

    report.finalize()
    return result


def _save_raw(
    row,
    col_idx: dict,
    row_number: int,
    source_file: str,
    error_message: str = "",
    import_report: ImportReport | None = None,
    academic_year: AcademicYear | None = None,
) -> RawImport:
    payload = {}
    for name, idx in col_idx.items():
        val = row[idx] if idx < len(row) else None
        payload[name] = str(val).strip() if val is not None else ""
    payload["row_number"] = row_number
    company = payload.get("Raison sociale", "")[:30]
    return RawImport.objects.create(
        source="excel_internships",
        source_file=source_file,
        external_id=f"row_{row_number}_{company}",
        payload=payload,
        entity=RawImportEntity.INTERNSHIP,
        status=RawImportStatus.FAILED if error_message else RawImportStatus.PENDING,
        error_message=error_message,
        import_report=import_report,
        academic_year=academic_year,
    )


def _parse_date(val: str | None):
    if not val:
        return None
    from datetime import datetime

    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None
