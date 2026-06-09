from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.utils import timezone

from app.academic.models import AcademicYear
from app.imports.models import (
    ImportReport as DbImportReport,
)
from app.imports.models import (
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.reference.models import Country, Department, Level, Parcours

from ..models import AnnualEnrollment, Student


@dataclass
class StudentRow:
    ine: str
    first_name: str
    last_name: str
    email: str
    department_code: str
    level_code: str
    parcours_code: str | None = None
    gpa: float | None = None
    gender: str = ""
    nationality_iso2: str | None = None
    # Source tracking (may be empty for Excel imports)
    source_id: str | None = None  # e.g. Pegase internal student ID
    source_sync_at: datetime | None = None  # timestamp from the source system


@dataclass
class ImportReport:
    created: int = 0
    updated: int = 0
    unresolved: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def import_students(
    rows: list[StudentRow],
    academic_year: AcademicYear,
    db_report: DbImportReport | None = None,
    source_file: str = "",
) -> ImportReport:
    report = ImportReport()

    dept_cache: dict[str, Department | None] = {}
    level_cache: dict[str, Level | None] = {}
    parcours_cache: dict[tuple, Parcours | None] = {}
    country_cache: dict[str, Country | None] = {}

    for row in rows:
        payload = {
            "ine": row.ine,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "gender": row.gender,
            "department_code": row.department_code,
            "level_code": row.level_code,
            "parcours_code": row.parcours_code,
            "gpa": str(row.gpa) if row.gpa is not None else None,
        }

        raw = RawImport(
            source="pegase" if not source_file else "excel_students",
            source_file=source_file,
            entity=RawImportEntity.STUDENT,
            external_id=row.ine,
            payload=payload,
            import_report=db_report,
            academic_year=academic_year,
        )

        try:
            department = _resolve_department(row.department_code, dept_cache)
            if department is None:
                reason = f"Département introuvable: {row.department_code}"
                report.unresolved.append({"ine": row.ine, "reason": reason})
                raw.status = RawImportStatus.FAILED
                raw.error_message = reason
                raw.save()
                if db_report:
                    db_report.record_error(row.ine, reason)
                continue

            level = _resolve_level(row.level_code, level_cache)
            if level is None:
                reason = f"Niveau introuvable: {row.level_code}"
                report.unresolved.append({"ine": row.ine, "reason": reason})
                raw.status = RawImportStatus.FAILED
                raw.error_message = reason
                raw.save()
                if db_report:
                    db_report.record_error(row.ine, reason)
                continue

            parcours = None
            if row.parcours_code:
                parcours = _resolve_parcours(
                    row.parcours_code, department, parcours_cache
                )
                if parcours is None:
                    reason = f"Parcours introuvable: {row.parcours_code} (dept: {row.department_code})"
                    report.unresolved.append({"ine": row.ine, "reason": reason})
                    raw.status = RawImportStatus.FAILED
                    raw.error_message = reason
                    raw.save()
                    if db_report:
                        db_report.record_error(row.ine, reason)
                    continue

            nationality = _resolve_country(row.nationality_iso2, country_cache)

            sync_now = row.source_sync_at or timezone.now()
            student, created = Student.objects.get_or_create(
                ine=row.ine,
                defaults={
                    "first_name": row.first_name,
                    "last_name": row.last_name,
                    "email": row.email,
                    "gender": row.gender,
                    "nationality": nationality,
                    "pegase_id": row.source_id,
                    "last_sync_pegase": sync_now,
                },
            )

            if not created:
                update_fields = []
                for attr in ("first_name", "last_name", "email", "gender"):
                    val = getattr(row, attr)
                    if val and getattr(student, attr) != val:
                        setattr(student, attr, val)
                        update_fields.append(attr)
                if nationality is not None and student.nationality != nationality:
                    student.nationality = nationality
                    update_fields.append("nationality")
                if row.source_id and student.pegase_id != row.source_id:
                    student.pegase_id = row.source_id
                    update_fields.append("pegase_id")
                student.last_sync_pegase = sync_now
                update_fields.append("last_sync_pegase")
                if update_fields:
                    student.save(update_fields=update_fields)

            enrollment, enrollment_created = AnnualEnrollment.objects.update_or_create(
                student=student,
                academic_year=academic_year,
                defaults={
                    "department": department,
                    "level": level,
                    "parcours": parcours,
                    "gpa": _to_decimal(row.gpa),
                },
            )
            enrollment.full_clean()

            raw.status = RawImportStatus.IMPORTED
            raw.imported_at = timezone.now()
            raw.save()

            if enrollment_created:
                report.created += 1
            else:
                report.updated += 1

            if db_report:
                db_report.record_success()

        except Exception as exc:  # noqa: BLE001
            msg = f"INE {row.ine}: {exc}"
            report.errors.append(msg)
            raw.status = RawImportStatus.FAILED
            raw.error_message = str(exc)
            if not raw.pk:
                raw.save()
            else:
                raw.save(update_fields=["status", "error_message", "updated_at"])
            if db_report:
                db_report.record_error(row.ine, str(exc))

    return report


def _resolve_department(
    code: str, cache: dict[str, Department | None]
) -> Department | None:
    if code not in cache:
        cache[code] = Department.objects.filter(code__iexact=code).first()
    return cache[code]


def _resolve_level(code: str, cache: dict[str, Level | None]) -> Level | None:
    if code not in cache:
        cache[code] = Level.objects.filter(code__iexact=code).first()
    return cache[code]


def _resolve_parcours(
    code: str, department: Department, cache: dict[tuple, Parcours | None]
) -> Parcours | None:
    key = (department.pk, code)
    if key not in cache:
        cache[key] = Parcours.objects.filter(
            department=department, code__iexact=code
        ).first()
    return cache[key]


def _resolve_country(
    nationality_raw: str | None, cache: dict[str, Country | None]
) -> Country | None:
    """
    Resolve a country from whatever Pegase/Excel provides: ISO2 code ("FR"),
    French name ("France", "france"), or English name ("France").
    """
    if not nationality_raw:
        return None
    key = nationality_raw.strip().lower()
    if key not in cache:
        raw = nationality_raw.strip()
        country = Country.objects.filter(iso2__iexact=raw).first()
        if country is None:
            country = Country.objects.filter(name_fr__iexact=raw).first()
        if country is None:
            country = Country.objects.filter(name_en__iexact=raw).first()
        cache[key] = country
    return cache[key]


def _to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None
