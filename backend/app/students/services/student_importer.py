from dataclasses import dataclass, field
from datetime import date, datetime
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
from app.shared.cleaning import (
    normalize_country_code,
    normalize_ine,
    normalize_string,
)
from app.shared.sync import already_up_to_date, touch_last_sync

from ..models import AnnualEnrollment, Student
from .student_validator import validate_student


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
    source_id: str | None = None
    source_sync_at: datetime | None = None
    # Position dans la source (ligne Excel, index Pégase) — sert de repli pour
    # external_id quand l'INE est vide, pour que chaque ligne sans INE reste
    # individuellement identifiable dans le panneau d'erreurs plutôt que
    # d'être fusionnée avec les autres sous un external_id "" commun.
    row_number: int | str | None = None
    # Erreur de parsing détectée par l'adaptateur (ex. GPA non numérique) —
    # la ligne est quand même transmise à import_students() plutôt que d'être
    # abandonnée en silence, pour finir en échec explicite dans le panneau
    # d'erreurs au lieu de disparaître sans laisser de trace.
    parse_error: str | None = None
    # None = non renseigné par la source (ex. Pégase ne fournit pas ces deux
    # champs) : on ne touche pas à la valeur existante dans ce cas plutôt que
    # d'écraser un statut Boursier/FISA saisi manuellement par un admin.
    is_alternant: bool | None = None
    is_scholarship: bool | None = None

    def __post_init__(self) -> None:
        self.ine = normalize_ine(self.ine)
        self.first_name = normalize_string(self.first_name)
        self.last_name = normalize_string(self.last_name)
        self.email = self.email.strip().lower() if self.email else ""
        self.department_code = normalize_string(self.department_code).upper()
        self.level_code = normalize_string(self.level_code).upper()
        if self.parcours_code:
            self.parcours_code = normalize_string(self.parcours_code).upper()
        if self.nationality_iso2:
            self.nationality_iso2 = normalize_country_code(self.nationality_iso2)


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
        # Une ligne sans INE ne doit pas être fusionnée avec les autres lignes
        # sans INE sous un même external_id "" — sinon list_student_import_errors
        # (qui déduplique par external_id) n'en affiche qu'une seule, faisant
        # disparaître les autres du panneau d'erreurs (perte d'information).
        external_id = (
            row.ine
            or f"row_{row.row_number if row.row_number is not None else id(row)}"
        )
        raw = RawImport(
            source="pegase" if not source_file else "excel_students",
            source_file=source_file,
            entity=RawImportEntity.STUDENT,
            external_id=external_id,
            payload={
                "ine": row.ine,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "email": row.email,
                "gender": row.gender,
                "department_code": row.department_code,
                "level_code": row.level_code,
                "parcours_code": row.parcours_code,
                "gpa": str(row.gpa) if row.gpa is not None else None,
                "nationality_iso2": row.nationality_iso2,
                "is_alternant": row.is_alternant,
                "is_scholarship": row.is_scholarship,
            },
            import_report=db_report,
            academic_year=academic_year,
        )

        try:
            validate_student(row)
            if row.parse_error:
                raise ValueError(row.parse_error)

            department = _resolve_department(row.department_code, dept_cache)
            if department is None:
                _mark_unresolved(
                    raw,
                    report,
                    db_report,
                    row.ine,
                    f"Département introuvable: {row.department_code}",
                )
                continue

            level = _resolve_level(row.level_code, level_cache)
            if level is None:
                _mark_unresolved(
                    raw,
                    report,
                    db_report,
                    row.ine,
                    f"Niveau introuvable: {row.level_code}",
                )
                continue

            parcours = None
            if row.parcours_code:
                parcours = _resolve_parcours(
                    row.parcours_code, department, parcours_cache
                )
                if parcours is None:
                    _mark_unresolved(
                        raw,
                        report,
                        db_report,
                        row.ine,
                        f"Parcours introuvable: {row.parcours_code} (dept: {row.department_code})",
                    )
                    continue

            nationality = _resolve_country(row.nationality_iso2, country_cache)
            sync_now = row.source_sync_at or timezone.now()
            source_date = row.source_sync_at.date() if row.source_sync_at else None

            student = _upsert_student(row, nationality, sync_now, source_date)
            enrollment_created, enrollment_changed = _upsert_enrollment(
                student,
                academic_year,
                department,
                level,
                parcours,
                _to_decimal(row.gpa),
                source_date,
                row.is_alternant,
                row.is_scholarship,
            )

            raw.status = RawImportStatus.IMPORTED
            raw.imported_at = timezone.now()
            raw.save()

            if enrollment_created:
                report.created += 1
            elif enrollment_changed:
                report.updated += 1

            if db_report:
                db_report.record_success()

        except Exception as exc:  # noqa: BLE001
            msg = f"INE {external_id}: {exc}"
            report.errors.append(msg)
            raw.status = RawImportStatus.FAILED
            raw.error_message = str(exc)
            if not raw.pk:
                raw.save()
            else:
                raw.save(update_fields=["status", "error_message", "updated_at"])
            if db_report:
                db_report.record_error(external_id, str(exc))

    return report


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------


def _mark_unresolved(
    raw: RawImport,
    report: ImportReport,
    db_report: DbImportReport | None,
    ine: str,
    reason: str,
) -> None:
    report.unresolved.append({"ine": ine, "reason": reason})
    raw.status = RawImportStatus.FAILED
    raw.error_message = reason
    raw.save()
    if db_report:
        db_report.record_error(ine, reason)


def _upsert_student(
    row: StudentRow,
    nationality: Country | None,
    sync_now: datetime,
    source_date: date | None,
) -> Student:
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

    if created:
        return student

    incoming: dict = {}
    for attr in ("first_name", "last_name", "email", "gender"):
        val = getattr(row, attr)
        if val:
            incoming[attr] = val
    if nationality is not None:
        incoming["nationality_id"] = nationality.pk
    if row.source_id:
        incoming["pegase_id"] = row.source_id

    if already_up_to_date(student, "last_sync_pegase", source_date, **incoming):
        return student

    update_fields: list[str] = []
    for attr in ("first_name", "last_name", "email", "gender"):
        val = getattr(row, attr)
        if val and getattr(student, attr) != val:
            setattr(student, attr, val)
            update_fields.append(attr)
    if nationality is not None and student.nationality_id != nationality.pk:
        student.nationality = nationality
        update_fields.append("nationality")
    if row.source_id and student.pegase_id != row.source_id:
        student.pegase_id = row.source_id
        update_fields.append("pegase_id")

    if update_fields:
        student.save(update_fields=update_fields)
        student.last_sync_pegase = student.updated_at
        student.save(update_fields=["last_sync_pegase"])
    else:
        touch_last_sync(student, "last_sync_pegase")

    return student


def _upsert_enrollment(
    student: Student,
    academic_year: AcademicYear,
    department: Department,
    level: Level,
    parcours: Parcours | None,
    new_gpa: Decimal | None,
    source_date: date | None,
    is_alternant: bool | None = None,
    is_scholarship: bool | None = None,
) -> tuple[bool, bool]:
    """Upsert AnnualEnrollment. Returns (created, changed).

    is_alternant/is_scholarship: None means the source didn't provide a value
    (e.g. Pégase) — the existing value is left untouched rather than reset to
    the model's False default.
    """
    enrollment, created = AnnualEnrollment.objects.get_or_create(
        student=student,
        academic_year=academic_year,
        defaults={
            "department": department,
            "level": level,
            "parcours": parcours,
            "gpa": new_gpa,
            "is_alternant": bool(is_alternant),
            "is_scholarship": bool(is_scholarship),
        },
    )

    if created:
        touch_last_sync(enrollment, "last_sync_pegase")
        enrollment.full_clean()
        return True, False

    tracked_fields: dict = {
        "department_id": department.pk,
        "level_id": level.pk,
        "parcours_id": parcours.pk if parcours else None,
        "gpa": new_gpa,
    }
    if is_alternant is not None:
        tracked_fields["is_alternant"] = is_alternant
    if is_scholarship is not None:
        tracked_fields["is_scholarship"] = is_scholarship

    if already_up_to_date(
        enrollment,
        "last_sync_pegase",
        source_date,
        **tracked_fields,
    ):
        enrollment.full_clean()
        return False, False

    updates: list[str] = []
    if enrollment.department_id != department.pk:
        enrollment.department = department
        updates.append("department")
    if enrollment.level_id != level.pk:
        enrollment.level = level
        updates.append("level")
    if enrollment.parcours_id != (parcours.pk if parcours else None):
        enrollment.parcours = parcours
        updates.append("parcours")
    if enrollment.gpa != new_gpa:
        enrollment.gpa = new_gpa
        updates.append("gpa")
    if is_alternant is not None and enrollment.is_alternant != is_alternant:
        enrollment.is_alternant = is_alternant
        updates.append("is_alternant")
    if is_scholarship is not None and enrollment.is_scholarship != is_scholarship:
        enrollment.is_scholarship = is_scholarship
        updates.append("is_scholarship")

    if updates:
        enrollment.save(update_fields=updates)
        enrollment.last_sync_pegase = enrollment.updated_at
        enrollment.save(update_fields=["last_sync_pegase"])
        enrollment.full_clean()
        return False, True

    touch_last_sync(enrollment, "last_sync_pegase")
    enrollment.full_clean()
    return False, False


# ---------------------------------------------------------------------------
# Cache-based resolution helpers
# ---------------------------------------------------------------------------


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
    """Resolve a country from ISO2 code, French name, or English name."""
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
