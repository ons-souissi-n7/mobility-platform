import logging
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
from app.mobility.models import Agreement, AgreementYear, NomenclatureMapping
from app.shared.cleaning import normalize_ine, normalize_string
from app.shared.sync import already_up_to_date
from app.shared.validators import DomainValidationError

from ..models import MAX_WISHES_PER_STUDENT, AnnualEnrollment, Student, StudentWish
from .student_validator import validate_wish

logger = logging.getLogger(__name__)


@dataclass
class WishRow:
    individu: str
    offre_de_sejour: str
    rank: int
    ine: str = ""
    moveon_offer_id: str = ""
    source_date: date | None = None

    def __post_init__(self) -> None:
        self.ine = normalize_ine(self.ine)
        self.individu = normalize_string(self.individu)
        self.offre_de_sejour = normalize_string(self.offre_de_sejour)


@dataclass
class WishSyncReport:
    created: int = 0
    updated: int = 0
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
        source=ImportSource.MOVEON_WISHES,
        academic_year=academic_year,
        triggered_by=triggered_by,
    )

    raw_records = client.fetch_student_wishes()

    rows: list[WishRow] = []
    skipped = 0

    for r in raw_records:
        if not ((r.ine or r.individu) and r.offre_de_sejour and r.rank > 0):
            continue

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
                moveon_offer_id=r.moveon_offer_id or "",
                source_date=r.date_modification or r.date_creation,
            )
        )

    report = import_wish_rows(rows, academic_year, db_report)
    report.skipped = skipped
    db_report.finalize()
    return report


def import_wish_rows(
    rows: list[WishRow],
    academic_year: AcademicYear,
    db_report: DbImportReport | None = None,
) -> WishSyncReport:
    report = WishSyncReport()

    student_cache: dict[str, Student | None] = {}
    agreement_cache: dict[str, Agreement | None] = {}
    agreement_year_cache: dict[int, AgreementYear | None] = {}

    # Pré-charger les rangs de vœux existants par inscription (évite N+1 en boucle)
    existing_ranks: dict[int, set[int]] = {}
    for eid, rank in (
        StudentWish.objects.filter(annual_enrollment__academic_year=academic_year)
        .values_list("annual_enrollment_id", "rank")
    ):
        existing_ranks.setdefault(eid, set()).add(rank)

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
                "moveon_offer_id": row.moveon_offer_id,
                "rank": row.rank,
            },
            import_report=db_report,
            academic_year=academic_year,
        )

        try:
            validate_wish(row)
        except DomainValidationError as exc:
            _mark_wish_unresolved(raw, report, db_report, row, identifier, str(exc))
            continue

        student = _resolve_student(row.ine, row.individu, student_cache)
        if student is None:
            reason = (
                f"Étudiant introuvable (INE : {row.ine!r}, Individu : {row.individu!r})"
            )
            _mark_wish_unresolved(raw, report, db_report, row, identifier, reason)
            continue

        enrollment = AnnualEnrollment.objects.filter(
            student=student, academic_year=academic_year
        ).first()
        if enrollment is None:
            reason = (
                f"Aucune inscription annuelle pour {student} en {academic_year}. "
                "Synchronisez d'abord les inscriptions depuis Pégase."
            )
            _mark_wish_unresolved(raw, report, db_report, row, identifier, reason)
            continue

        agreement = _resolve_agreement(
            row.offre_de_sejour, row.moveon_offer_id, agreement_cache
        )
        if agreement is None:
            reason = (
                f"Accord introuvable (Offre de séjour : {row.offre_de_sejour!r}). "
                "Vérifiez que cet accord a été synchronisé depuis MoveON avec ce nom "
                "ou qu'il a été créé manuellement avec ce même intitulé."
            )
            _mark_wish_unresolved(raw, report, db_report, row, identifier, reason)
            continue

        agreement_year = _resolve_agreement_year(
            agreement, academic_year, agreement_year_cache
        )
        if agreement_year is None:
            reason = (
                f"Aucun slot annuel pour l'accord {agreement.name!r} en {academic_year}. "
                "Initialisez les accords de cette année via Mobilité > Initialiser l'année."
            )
            _mark_wish_unresolved(raw, report, db_report, row, identifier, reason)
            continue

        if row.rank > MAX_WISHES_PER_STUDENT:
            reason = (
                f"Rang {row.rank} refusé : maximum {MAX_WISHES_PER_STUDENT} vœux par étudiant."
            )
            _mark_wish_unresolved(raw, report, db_report, row, identifier, reason)
            continue

        current_count = len(existing_ranks.get(enrollment.id, set()) - {row.rank})
        if current_count >= MAX_WISHES_PER_STUDENT:
            reason = (
                f"Vœu refusé : l'étudiant {identifier!r} a déjà {MAX_WISHES_PER_STUDENT} vœux enregistrés."
            )
            _mark_wish_unresolved(raw, report, db_report, row, identifier, reason)
            continue

        existing_wish = StudentWish.objects.filter(
            annual_enrollment=enrollment, rank=row.rank
        ).first()
        if existing_wish is not None and already_up_to_date(
            existing_wish,
            "last_sync_moveon",
            row.source_date,
            agreement_year_id=agreement_year.pk,
        ):
            raw.status = RawImportStatus.IMPORTED
            raw.save()
            if db_report:
                db_report.record_success()
            continue

        try:
            wish, created = StudentWish.objects.update_or_create(
                annual_enrollment=enrollment,
                rank=row.rank,
                defaults={"agreement_year": agreement_year},
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

        wish.last_sync_moveon = wish.updated_at
        wish.save(update_fields=["last_sync_moveon"])

        existing_ranks.setdefault(enrollment.id, set()).add(row.rank)

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


def _mark_wish_unresolved(
    raw: RawImport,
    report: WishSyncReport,
    db_report: DbImportReport | None,
    row: WishRow,
    identifier: str,
    reason: str,
) -> None:
    report.unresolved.append(
        {"individu": row.individu, "ine": row.ine, "rank": row.rank, "reason": reason}
    )
    raw.status = RawImportStatus.FAILED
    raw.error_message = reason
    raw.save()
    if db_report:
        db_report.record_error(identifier, reason)


def _in_year_window(d: date | None, academic_year: AcademicYear) -> bool:
    """
    Returns True if d is within [academic_year.start_date - 12 months, academic_year.end_date].

    The 12-month lookback covers wish-submission campaigns that run the semester
    before the academic year starts.  If d is None the record is always included.
    """
    if d is None:
        return True
    try:
        window_start = academic_year.start_date.replace(
            year=academic_year.start_date.year - 1
        )
    except ValueError:  # Leap-year edge case (Feb 29)
        window_start = academic_year.start_date.replace(
            year=academic_year.start_date.year - 1, day=28
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
                matches = Student.objects.filter(
                    last_name__iexact=parts[0],
                    first_name__iexact=parts[1],
                )
                count = matches.count()
                if count > 1:
                    logger.warning(
                        "Homonyme détecté : %d étudiants correspondent à '%s' — "
                        "le premier résultat sera utilisé (résolution ambiguë)",
                        count, individu,
                    )
                student = matches.first()
            else:
                student = Student.objects.filter(last_name__iexact=individu).first()
        cache[cache_key] = student
    return cache[cache_key]


def _resolve_agreement(
    offre: str,
    moveon_offer_id: str,
    cache: dict[str, Agreement | None],
) -> Agreement | None:
    """
    Résolution en 3 étapes, de la plus fiable à la plus souple :

    1. Par moveon_id (ID stable fourni par MoveON dans le vœu) — le plus rapide.
    2. Par nom exact de l'accord (insensible à la casse).
    3. Par NomenclatureMapping.moveon_offer_name — accords créés manuellement.

    Si l'accord est trouvé et que son moveon_id est vide, on le renseigne
    automatiquement pour accélérer les recherches futures.
    """
    if offre in cache:
        return cache[offre]

    agreement: Agreement | None = None

    if moveon_offer_id:
        agreement = Agreement.objects.filter(moveon_id=moveon_offer_id).first()

    if agreement is None and offre:
        agreement = Agreement.objects.filter(moveon_id=offre.strip()).first()

    if agreement is None:
        agreement = Agreement.objects.filter(name__iexact=offre).first()

    if agreement is None:
        mapping = (
            NomenclatureMapping.objects.filter(moveon_offer_name__iexact=offre)
            .select_related("agreement")
            .first()
        )
        if mapping is not None:
            agreement = mapping.agreement

    if agreement is not None and moveon_offer_id and not agreement.moveon_id:
        agreement.moveon_id = moveon_offer_id
        agreement.save(update_fields=["moveon_id", "updated_at"])

    cache[offre] = agreement
    return agreement


def _resolve_agreement_year(
    agreement: Agreement,
    academic_year: AcademicYear,
    cache: dict[int, AgreementYear | None],
) -> AgreementYear | None:
    if agreement.pk not in cache:
        cache[agreement.pk] = AgreementYear.objects.filter(
            agreement=agreement, academic_year=academic_year
        ).first()
    return cache[agreement.pk]
