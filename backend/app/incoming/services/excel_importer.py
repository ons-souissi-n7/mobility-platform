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

from ..models import IncomingStudent
from .date_utils import _parse_date

logger = logging.getLogger(__name__)

_COLUMNS = [
    "DEPARTEMENT",
    "CIVILITE",
    "NOM",
    "PRENOM",
    "PAYS",
    "UNIV ORIGINE",
    "DATE NAISSANCE",
    "CADRE",
    "MAIL",
    "MAIL ENSEEIHT",
    "DUREE",
    "ANNEE",
    "PARCOURS",
    "REMARQUES",
    "STAGE",
    "DIPLOME",
    "POURSUITE DOCTORAT",
]


@dataclass
class ExcelImportResult:
    total: int = 0
    created: int = 0
    updated: int = 0
    failed: int = 0
    duplicates: int = 0


def import_incoming_from_excel(
    file_bytes: bytes,
    source_file: str,
    academic_year: AcademicYear,
    triggered_by: str = "",
) -> ExcelImportResult:
    import openpyxl

    from app.institutions.models import PartnerUniversity
    from app.mobility.models import MobilityCategory
    from app.reference.models import Country, Department, Level, Parcours

    result = ExcelImportResult()
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

    header = [str(c).strip().upper() if c else "" for c in rows[0]]
    col_idx: dict[str, int] = {}
    for name in _COLUMNS:
        try:
            col_idx[name] = header.index(name)
        except ValueError:
            pass

    def _get(row, name: str) -> str:
        idx = col_idx.get(name)
        if idx is None or idx >= len(row):
            return ""
        val = row[idx]
        return str(val).strip() if val is not None else ""

    def _get_raw(row, name: str):
        idx = col_idx.get(name)
        if idx is None or idx >= len(row):
            return None
        return row[idx]

    country_cache: dict[str, Country | None] = {}
    dept_cache: dict[str, Department | None] = {}
    univ_cache: dict[str, PartnerUniversity | None] = {}
    cat_cache: dict[str, MobilityCategory | None] = {}
    level_cache: dict[str, Level | None] = {}
    parcours_cache: dict[str, Parcours | None] = {}

    done_external_ids = frozenset(
        RawImport.objects.filter(
            source="excel_incoming",
            academic_year=academic_year,
            status__in=[RawImportStatus.IGNORED, RawImportStatus.IMPORTED],
        ).values_list("external_id", flat=True)
    )

    for row_number, row in enumerate(rows[1:], start=2):
        if all(v is None or str(v).strip() == "" for v in row):
            continue
        result.total += 1
        last_name = _get(row, "NOM")
        first_name = _get(row, "PRENOM")
        external_id = f"row_{row_number}_{last_name[:20]}_{first_name[:20]}"

        if external_id in done_external_ids:
            result.updated += 1
            continue

        if not last_name or not first_name:
            result.failed += 1
            error_msg = "Nom ou prénom manquant."
            _save_raw(
                row, col_idx, row_number, source_file, error_msg, report, academic_year
            )
            report.record_error(external_id, error_msg)
            continue

        raw = _save_raw(
            row, col_idx, row_number, source_file, "", report, academic_year
        )

        birth_date = _parse_date(_get_raw(row, "DATE NAISSANCE"))

        # Check duplicate
        existing_student = (
            IncomingStudent.objects.filter(
                academic_year=academic_year,
                last_name__iexact=last_name,
                first_name__iexact=first_name,
                birth_date=birth_date,
            )
            .select_related(
                "country", "department", "mobility_category", "level", "parcours"
            )
            .first()
        )
        if existing_student:
            result.duplicates += 1
            error_msg = (
                f"Doublon : {last_name} {first_name} déjà présent pour cette année."
            )
            raw.payload = {
                **raw.payload,
                "_existing": {
                    "NOM": existing_student.last_name,
                    "PRENOM": existing_student.first_name,
                    "CIVILITE": existing_student.civility or "",
                    "PAYS": existing_student.country.name_fr
                    if existing_student.country
                    else "",
                    "DEPARTEMENT": existing_student.department.code
                    if existing_student.department
                    else "",
                    "DATE NAISSANCE": str(existing_student.birth_date)
                    if existing_student.birth_date
                    else "",
                    "UNIV ORIGINE": existing_student.origin_university_name or "",
                    "MAIL": existing_student.personal_email or "",
                    "MAIL ENSEEIHT": existing_student.n7_email or "",
                    "DUREE": existing_student.duration or "",
                    "CADRE": existing_student.mobility_category.name
                    if existing_student.mobility_category
                    else "",
                    "ANNEE": existing_student.level.code
                    if existing_student.level
                    else "",
                    "PARCOURS": existing_student.parcours.code
                    if existing_student.parcours
                    else "",
                },
            }
            raw.status = RawImportStatus.CONFLICT
            raw.error_message = error_msg
            raw.save(update_fields=["status", "error_message", "payload", "updated_at"])
            report.record_conflict(external_id, error_msg, raw.id)
            continue

        # Resolve references
        country_name = _get(row, "PAYS")
        if country_name not in country_cache:
            c = Country.objects.filter(name_fr__iexact=country_name).first()
            if c is None:
                c = Country.objects.filter(name_en__iexact=country_name).first()
            country_cache[country_name] = c

        dept_code = _get(row, "DEPARTEMENT")
        if dept_code not in dept_cache:
            dept_cache[dept_code] = Department.objects.filter(
                code__iexact=dept_code
            ).first()

        univ_name = _get(row, "UNIV ORIGINE")
        if univ_name not in univ_cache:
            univ_cache[univ_name] = (
                PartnerUniversity.objects.filter(name__iexact=univ_name).first()
                or PartnerUniversity.objects.filter(
                    short_name__iexact=univ_name
                ).first()
            )

        cat_name = _get(row, "CADRE")
        if cat_name not in cat_cache:
            cat_cache[cat_name] = MobilityCategory.objects.filter(
                name__iexact=cat_name
            ).first()

        level_code = _get(row, "ANNEE")
        if level_code not in level_cache:
            level_cache[level_code] = Level.objects.filter(
                code__iexact=level_code
            ).first()

        parcours_code = _get(row, "PARCOURS")
        if parcours_code not in parcours_cache:
            parcours_cache[parcours_code] = Parcours.objects.filter(
                code__iexact=parcours_code
            ).first()

        doctoral_raw = _get(row, "POURSUITE DOCTORAT").lower()
        doctoral_continuation = doctoral_raw in ("o", "oui", "yes", "1", "true", "vrai")

        try:
            IncomingStudent.objects.create(
                academic_year=academic_year,
                department=dept_cache.get(dept_code),
                civility=_get(row, "CIVILITE"),
                last_name=last_name,
                first_name=first_name,
                country=country_cache.get(country_name),
                origin_university=univ_cache.get(univ_name),
                origin_university_name=univ_name,
                birth_date=birth_date,
                mobility_category=cat_cache.get(cat_name),
                personal_email=_get(row, "MAIL"),
                n7_email=_get(row, "MAIL ENSEEIHT"),
                duration=_get(row, "DUREE"),
                level=level_cache.get(level_code),
                parcours=parcours_cache.get(parcours_code),
                remarks=_get(row, "REMARQUES"),
                internship_info=_get(row, "STAGE"),
                diploma_info=_get(row, "DIPLOME"),
                doctoral_continuation=doctoral_continuation,
            )
            raw.status = RawImportStatus.IMPORTED
            raw.imported_at = timezone.now()
            raw.save(update_fields=["status", "imported_at", "updated_at"])
            result.created += 1
            report.record_success()
        except IntegrityError:
            result.duplicates += 1
            error_msg = (
                f"Doublon : {last_name} {first_name} déjà présent pour cette année."
            )
            existing = (
                IncomingStudent.objects.filter(
                    academic_year=academic_year,
                    last_name=last_name,
                    first_name=first_name,
                    birth_date=birth_date,
                )
                .select_related(
                    "country", "department", "mobility_category", "level", "parcours"
                )
                .first()
            )
            if existing:
                raw.payload = {
                    **raw.payload,
                    "_existing": {
                        "NOM": existing.last_name,
                        "PRENOM": existing.first_name,
                        "CIVILITE": existing.civility or "",
                        "PAYS": existing.country.name_fr if existing.country else "",
                        "DEPARTEMENT": existing.department.code
                        if existing.department
                        else "",
                        "DATE NAISSANCE": str(existing.birth_date)
                        if existing.birth_date
                        else "",
                        "UNIV ORIGINE": existing.origin_university_name or "",
                        "MAIL": existing.personal_email or "",
                        "MAIL ENSEEIHT": existing.n7_email or "",
                        "DUREE": existing.duration or "",
                        "CADRE": existing.mobility_category.name
                        if existing.mobility_category
                        else "",
                        "ANNEE": existing.level.code if existing.level else "",
                        "PARCOURS": existing.parcours.code if existing.parcours else "",
                    },
                }
            raw.status = RawImportStatus.CONFLICT
            raw.error_message = error_msg
            raw.save(update_fields=["status", "error_message", "payload", "updated_at"])
            report.record_conflict(external_id, error_msg, raw.id)
        except Exception as exc:
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
    payload: dict = {}
    for name, idx in col_idx.items():
        val = row[idx] if idx < len(row) else None
        payload[name] = str(val).strip() if val is not None else ""
    payload["row_number"] = row_number
    nom = payload.get("NOM", "")[:20]
    prenom = payload.get("PRENOM", "")[:20]
    return RawImport.objects.create(
        source="excel_incoming",
        source_file=source_file,
        external_id=f"row_{row_number}_{nom}_{prenom}",
        payload=payload,
        entity=RawImportEntity.INCOMING_STUDENT,
        status=RawImportStatus.FAILED if error_message else RawImportStatus.PENDING,
        error_message=error_message,
        import_report=import_report,
        academic_year=academic_year,
    )
