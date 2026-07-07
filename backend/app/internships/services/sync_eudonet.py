from __future__ import annotations

import logging
from dataclasses import dataclass, field

from django.db import IntegrityError
from django.utils import timezone

from app.academic.models import AcademicYear
from app.imports.models import (
    ImportReport as DbImportReport,
)
from app.imports.models import (
    ImportSource,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.integrations.eudonet import EudonetClient, EudonetInternship
from app.reference.models import Country
from app.shared.validators import DomainValidationError
from app.students.models import Student

from ..models import Internship
from .eudonet_validator import validate_internship_row

logger = logging.getLogger(__name__)

_COMPOSANTE_ENSEEIHT = {"enseeiht", "n7", "inp-enseeiht"}


@dataclass
class InternshipSyncReport:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    unresolved: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.updated + len(self.unresolved) + len(self.errors)


def sync_eudonet_internships(
    academic_year: AcademicYear,
    client: EudonetClient | None = None,
    triggered_by: str = "",
) -> InternshipSyncReport:
    client = client or EudonetClient()

    db_report = DbImportReport.objects.create(
        source=ImportSource.EUDONET,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    raw_records = client.fetch_internships()

    rows: list[EudonetInternship] = []
    skipped = 0

    for r in raw_records:
        if not r.is_international:
            skipped += 1
            continue
        if r.status_code != "9":
            skipped += 1
            continue
        if r.composante.lower() not in _COMPOSANTE_ENSEEIHT:
            skipped += 1
            continue
        rows.append(r)

    report = import_internship_rows(rows, academic_year, db_report)
    report.skipped = skipped
    db_report.finalize()
    return report


def import_internship_rows(
    rows: list[EudonetInternship],
    academic_year: AcademicYear,
    db_report: DbImportReport | None = None,
) -> InternshipSyncReport:
    report = InternshipSyncReport()

    student_cache: dict[str, Student | None] = {}
    country_cache: dict[str, Country | None] = {}

    for row in rows:
        external_id = f"{row.ine}#{row.company_name[:30]}#{row.start_date}"
        raw = RawImport(
            source="eudonet_internships",
            source_file="",
            entity=RawImportEntity.INTERNSHIP,
            external_id=external_id,
            payload={
                "ine": row.ine,
                "libelle": row.libelle,
                "company_name": row.company_name,
                "country_name": row.country_name,
                "city": row.city,
                "internship_type": row.internship_type,
                "status": row.status,
                "status_code": row.status_code,
                "start_date": str(row.start_date) if row.start_date else None,
                "end_date": str(row.end_date) if row.end_date else None,
                "weeks": row.weeks,
                "school_tutor": row.school_tutor,
                "company_tutor": row.company_tutor,
                "title": row.title,
            },
            import_report=db_report,
            academic_year=academic_year,
        )

        try:
            validate_internship_row(row)
        except DomainValidationError as exc:
            _mark_unresolved(raw, report, db_report, row.ine, str(exc))
            continue

        student = _resolve_student(row.ine, student_cache)
        if student is None:
            reason = f"Étudiant introuvable (INE : {row.ine!r})"
            _mark_unresolved(raw, report, db_report, row.ine, reason)
            continue

        country = _resolve_country(row.country_name, country_cache)

        internship_year = _resolve_academic_year(row.start_date, academic_year)

        try:
            internship, created = Internship.objects.update_or_create(
                student=student,
                company_name=row.company_name,
                start_date=row.start_date,
                defaults={
                    "academic_year": internship_year,
                    "country": country,
                    "city": row.city,
                    "title": row.title,
                    "internship_type": row.internship_type,
                    "status_code": row.status_code,
                    "status_label": row.status,
                    "end_date": row.end_date,
                    "weeks_in_company": row.weeks,
                    "school_tutor": row.school_tutor,
                    "company_tutor": row.company_tutor,
                    "eudonet_label": row.libelle,
                    "last_sync_eudonet": timezone.now(),
                },
            )
        except IntegrityError as exc:
            reason = f"Conflit ({row.ine!r}, {row.company_name!r}) : {exc}"
            report.errors.append(reason)
            raw.status = RawImportStatus.FAILED
            raw.error_message = reason
            raw.save()
            if db_report:
                db_report.record_error(external_id, reason)
            continue

        raw.status = RawImportStatus.IMPORTED
        raw.save()

        if created:
            report.created += 1
        else:
            report.updated += 1

        if db_report:
            db_report.record_success()

    return report


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _mark_unresolved(
    raw: RawImport,
    report: InternshipSyncReport,
    db_report: DbImportReport | None,
    identifier: str,
    reason: str,
) -> None:
    report.unresolved.append({"ine": identifier, "reason": reason})
    raw.status = RawImportStatus.FAILED
    raw.error_message = reason
    raw.save()
    if db_report:
        db_report.record_error(identifier, reason)


def _resolve_student(
    ine: str,
    cache: dict[str, Student | None],
) -> Student | None:
    if ine not in cache:
        cache[ine] = Student.objects.filter(ine=ine).first()
    return cache[ine]


def _resolve_country(
    name: str,
    cache: dict[str, Country | None],
) -> Country | None:
    if not name:
        return None
    if name not in cache:
        country = Country.objects.filter(name_fr__iexact=name).first()
        if country is None:
            country = Country.objects.filter(name_en__iexact=name).first()
        if country is None:
            logger.warning("Pays introuvable : %r", name)
        cache[name] = country
    return cache[name]


def _resolve_academic_year(
    start_date,
    fallback: AcademicYear,
) -> AcademicYear:
    if start_date is None:
        return fallback
    year = AcademicYear.objects.filter(
        start_date__lte=start_date,
        end_date__gte=start_date,
    ).first()
    return year if year is not None else fallback
