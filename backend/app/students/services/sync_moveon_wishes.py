from dataclasses import dataclass, field
from datetime import date

from django.db import IntegrityError

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
from app.integrations.moveon import MoveOnClient
from app.mobility.models import Agreement

from ..models import AnnualEnrollment, Student, StudentWish


@dataclass
class WishRow:
    # "MARTIN Jean" — MoveOn: Individu (used as name fallback)
    individu: str
    # agreement name — MoveOn: Offre de séjour
    offre_de_sejour: str
    rank: int
    # student INE — MoveOn: Numéro étudiant (primary match, may be empty)
    ine: str = ""


@dataclass
class WishSyncReport:
    created: int = 0
    updated: int = 0
    # Records whose creation/modification date falls outside the academic year window
    skipped: int = 0
    unresolved: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.updated + len(self.unresolved) + len(self.errors)


def sync_moveon_wishes(
    academic_year: AcademicYear,
    client: MoveOnClient | None = None,
    triggered_by: str = "",
) -> WishSyncReport:
    client = client or MoveOnClient()

    db_report = DbImportReport.objects.create(
        source=ImportSource.MOVEON_ACCORDS,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    raw_records = client.fetch_student_wishes()

    # MoveOn does not expose academic year labels, so we filter by date.
    # Records whose most recent date (creation or modification) falls outside
    # the academic year window [start - 12 months, end] are skipped.
    rows: list[WishRow] = []
    skipped = 0

    for r in raw_records:
        if not ((r.ine or r.individu) and r.offre_de_sejour and r.rank > 0):
            continue  # Malformed record

        record_date = r.date_creation or r.date_modification
        if not _in_year_window(record_date, academic_year):
            skipped += 1
            continue

        rows.append(
            WishRow(
                individu=r.individu,
                offre_de_sejour=r.offre_de_sejour,
                rank=r.rank,
                ine=r.ine,
            )
        )

    report = _import_wish_rows(rows, academic_year, db_report)
    report.skipped = skipped
    db_report.finalize()
    return report


def import_wish_rows(
    rows: list[WishRow],
    academic_year: AcademicYear,
    db_report: DbImportReport | None = None,
) -> WishSyncReport:
    return _import_wish_rows(rows, academic_year, db_report)


def _import_wish_rows(
    rows: list[WishRow],
    academic_year: AcademicYear,
    db_report: DbImportReport | None = None,
) -> WishSyncReport:
    report = WishSyncReport()

    student_cache: dict[str, Student | None] = {}
    agreement_cache: dict[str, Agreement | None] = {}

    for row in rows:
        identifier = row.ine or row.individu
        raw = RawImport(
            source="moveon_student_wishes",
            source_file="",
            entity=RawImportEntity.STUDENT,
            external_id=f"{identifier}#rank{row.rank}",
            payload={
                "ine": row.ine,
                "individu": row.individu,
                "offre_de_sejour": row.offre_de_sejour,
                "rank": row.rank,
            },
            import_report=db_report,
            academic_year=academic_year,
        )

        student = _resolve_student(row.ine, row.individu, student_cache)
        if student is None:
            reason = (
                f"Étudiant introuvable "
                f"(INE : {row.ine!r}, Individu : {row.individu!r})"
            )
            report.unresolved.append(
                {
                    "individu": row.individu,
                    "ine": row.ine,
                    "rank": row.rank,
                    "reason": reason,
                }
            )
            raw.status = RawImportStatus.FAILED
            raw.error_message = reason
            raw.save()
            if db_report:
                db_report.record_error(identifier, reason)
            continue

        enrollment = AnnualEnrollment.objects.filter(
            student=student, academic_year=academic_year
        ).first()
        if enrollment is None:
            reason = (
                f"Aucune inscription annuelle pour {student} en {academic_year}. "
                "Synchronisez d'abord les inscriptions depuis Pégase."
            )
            report.unresolved.append(
                {
                    "individu": row.individu,
                    "ine": row.ine,
                    "rank": row.rank,
                    "reason": reason,
                }
            )
            raw.status = RawImportStatus.FAILED
            raw.error_message = reason
            raw.save()
            if db_report:
                db_report.record_error(identifier, reason)
            continue

        agreement = _resolve_agreement(row.offre_de_sejour, agreement_cache)
        if agreement is None:
            reason = (
                f"Accord introuvable (Offre de séjour : {row.offre_de_sejour!r}). "
                "Vérifiez que cet accord a été synchronisé depuis MoveON avec ce nom "
                "ou qu'il a été créé manuellement avec ce même intitulé."
            )
            report.unresolved.append(
                {
                    "individu": row.individu,
                    "ine": row.ine,
                    "rank": row.rank,
                    "reason": reason,
                }
            )
            raw.status = RawImportStatus.FAILED
            raw.error_message = reason
            raw.save()
            if db_report:
                db_report.record_error(identifier, reason)
            continue

        try:
            _, created = StudentWish.objects.update_or_create(
                annual_enrollment=enrollment,
                rank=row.rank,
                defaults={"agreement": agreement},
            )
        except IntegrityError as exc:
            reason = f"Conflit de vœu ({identifier!r}, rang {row.rank}) : {exc}"
            report.errors.append(reason)
            raw.status = RawImportStatus.FAILED
            raw.error_message = reason
            raw.save()
            if db_report:
                db_report.record_error(identifier, reason)
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


def _in_year_window(d: date | None, academic_year: AcademicYear) -> bool:
    """
    Returns True if d is within [academic_year.start_date - 12 months, academic_year.end_date].

    The 12-month lookback covers the wish-submission campaign, which typically
    runs the semester before the academic year starts (e.g., November–February
    for a September start).

    If d is None (external system did not provide a date), the record is
    included by default so we never silently drop data.
    """
    if d is None:
        return True
    try:
        window_start = academic_year.start_date.replace(
            year=academic_year.start_date.year - 1
        )
    except ValueError:  # Leap-year edge case (Feb 29)
        window_start = academic_year.start_date.replace(
            year=academic_year.start_date.year - 1,
            day=28,
        )
    return window_start <= d <= academic_year.end_date


def _resolve_student(
    ine: str,
    individu: str,
    cache: dict[str, Student | None],
) -> Student | None:
    """
    Resolution order:
    1. Exact match on INE (when MoveOn provides "Numéro étudiant").
    2. Fallback: match on "NOM Prénom" from the Individu field (case-insensitive).
    """
    cache_key = ine if ine else individu
    if cache_key not in cache:
        student = None
        if ine:
            student = Student.objects.filter(ine=ine).first()
        if student is None and individu:
            parts = individu.strip().split(" ", 1)
            if len(parts) == 2:
                student = Student.objects.filter(
                    last_name__iexact=parts[0],
                    first_name__iexact=parts[1],
                ).first()
            else:
                student = Student.objects.filter(last_name__iexact=individu).first()
        cache[cache_key] = student
    return cache[cache_key]


def _resolve_agreement(
    offre: str, cache: dict[str, Agreement | None]
) -> Agreement | None:
    """
    1. Try exact match on Agreement.name (case-insensitive) — covers agreements synced from MoveOn.
    2. Fallback: try Agreement.moveon_id — covers manually-created agreements whose
       "Offre de séjour" name happens to equal the stored moveon_id.
    """
    if offre not in cache:
        agreement = Agreement.objects.filter(name__iexact=offre).first()
        if agreement is None:
            agreement = Agreement.objects.filter(moveon_id=offre).first()
        cache[offre] = agreement
    return cache[offre]
