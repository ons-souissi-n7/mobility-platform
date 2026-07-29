import logging

from django.db import transaction
from django_fsm import TransitionNotAllowed

from app.academic.models import AcademicYear
from app.alerts.models import SystemAlert
from app.audit.logger import log_action
from app.mobility.models import AgreementYear

from .gale_shapley import AgreementInput, StudentInput, gale_shapley

logger = logging.getLogger(__name__)


def run_gale_shapley(year_id: int, triggered_by: str = "") -> None:
    from app.outgoing.models import Assignment, AssignmentResult, AssignmentStatus
    from app.students.models import AnnualEnrollment, StudentWish

    try:
        academic_year = AcademicYear.objects.get(pk=year_id)
    except AcademicYear.DoesNotExist as exc:
        raise ValueError(f"Année académique {year_id} introuvable.") from exc

    # Guard : avorter si un Assignment non annulé existe déjà pour cette année.
    # Cas typique : retry Django-Q après timeout alors que la première exécution a abouti.
    if (
        Assignment.objects.filter(academic_year=academic_year)
        .exclude(status=AssignmentStatus.CANCELLED)
        .exists()
    ):
        logger.warning(
            "Un Assignment non annulé existe déjà pour l'année %s — "
            "arrêt pour éviter les doublons (retry Django-Q ?)",
            academic_year.label,
        )
        return

    # ── Charger les accords actifs pour cette année ───────────────────────
    agreement_years = (
        AgreementYear.objects.filter(
            academic_year=academic_year,
            is_active=True,
            n7_places__gt=0,
        )
        .select_related("agreement")
        .prefetch_related(
            "department_quotas__agreement_department__department",
            "agreement__levels",
        )
    )

    agreement_inputs: list[AgreementInput] = []
    ay_level_ids: dict[int, list[int]] = {}
    for ay in agreement_years:
        quota_dept: dict[int, int] = {}
        for dq in ay.department_quotas.all():
            dept_id = dq.agreement_department.department_id
            quota_dept[dept_id] = dq.get_effective_quota()
        level_ids = [lv.id for lv in ay.agreement.levels.all()]
        ay_level_ids[ay.id] = level_ids
        agreement_inputs.append(
            AgreementInput(
                agreement_year_id=ay.id,
                n7_places=ay.n7_places,
                quota_dept=quota_dept,
                level_ids=level_ids,
            )
        )

    # ── Charger les étudiants et leurs vœux ──────────────────────────────
    enrollments = AnnualEnrollment.objects.filter(
        academic_year=academic_year
    ).select_related("student__nationality", "department")

    enrollment_level: dict[int, int | None] = {e.id: e.level_id for e in enrollments}

    wishes_qs = (
        StudentWish.objects.filter(
            annual_enrollment__academic_year=academic_year,
        )
        .select_related("annual_enrollment")
        .order_by("annual_enrollment_id", "rank")
    )

    wishes_by_enrollment: dict[int, list[int]] = {}
    enrollments_with_wishes: set[int] = set()
    for wish in wishes_qs:
        eid = wish.annual_enrollment_id
        ay_id = wish.agreement_year_id
        enrollments_with_wishes.add(eid)
        # Filtre de niveau : exclure les vœux incompatibles avec le niveau de l'étudiant
        allowed_levels = ay_level_ids.get(ay_id, [])
        student_level = enrollment_level.get(eid)
        if (
            allowed_levels
            and student_level is not None
            and student_level not in allowed_levels
        ):
            continue
        wishes_by_enrollment.setdefault(eid, []).append(ay_id)

    # Étudiants dont tous les vœux ont été filtrés (niveau incompatible) : ils
    # sont traités comme un rejet total plutôt qu'ignorés — l'algorithme leur
    # cherche une destination alternative et documente le cas via un
    # AssignmentResult.system_note (cf. gale_shapley.StudentInput.level_mismatch).
    # enrollments_with_wishes est collecté dans la boucle ci-dessus (évite une 2e requête DB)
    level_mismatch_enrollments = enrollments_with_wishes - set(
        wishes_by_enrollment.keys()
    )

    student_inputs: list[StudentInput] = []
    for enrollment in enrollments:
        prefs = wishes_by_enrollment.get(enrollment.id, [])
        level_mismatch = enrollment.id in level_mismatch_enrollments
        if not prefs and not level_mismatch:
            continue
        nationality = enrollment.student.nationality
        is_french = nationality is not None and nationality.iso2 == "FR"
        gpa = float(enrollment.gpa) if enrollment.gpa is not None else None
        student_inputs.append(
            StudentInput(
                enrollment_id=enrollment.id,
                dept_id=enrollment.department_id,
                is_french=is_french,
                gpa=gpa,
                preferences=prefs,
                level_id=enrollment.level_id,
                level_mismatch=level_mismatch,
            )
        )

    # ── Lancer l'algorithme ───────────────────────────────────────────────
    outputs = gale_shapley(student_inputs, agreement_inputs)

    # ── Sauvegarder les résultats atomiquement ────────────────────────────
    assigned = sum(1 for o in outputs if o.agreement_year_id is not None)
    unassigned = sum(1 for o in outputs if o.agreement_year_id is None)

    with transaction.atomic():
        assignment = Assignment.objects.create(
            academic_year=academic_year,
            run_by=triggered_by,
            total_students=len(outputs),
            assigned_count=assigned,
            unassigned_count=unassigned,
        )

        AssignmentResult.objects.bulk_create(
            [
                AssignmentResult(
                    assignment=assignment,
                    annual_enrollment_id=output.enrollment_id,
                    agreement_year_id=output.agreement_year_id,
                    slot_type=output.slot_type,
                    assigned_rank=output.assigned_rank,
                    system_note=output.note,
                )
                for output in outputs
            ]
        )

    # Transition automatique pre_assignment → validation
    # select_for_update() requiert une transaction active — wrapper dans atomic()
    with transaction.atomic():
        academic_year = AcademicYear.objects.select_for_update().get(pk=year_id)
        if academic_year.status == AcademicYear.CampaignStatus.PRE_ASSIGNMENT:
            try:
                academic_year.complete_assignment()
                academic_year.save(update_fields=["status", "updated_at"])
            except TransitionNotAllowed:
                logger.error(
                    "complete_assignment refused for year %s (status=%s) — possible race condition",
                    academic_year.label,
                    academic_year.status,
                )
                SystemAlert.objects.create(
                    level="error",
                    title=f"Transition automatique échouée — {academic_year.label}",
                    message=(
                        f"L'algorithme Gale-Shapley a terminé pour {academic_year.label} "
                        f"mais la transition pre_assignment → validation a été refusée "
                        f"(état actuel : {academic_year.status}). "
                        f"Utilisez l'endpoint /academic/years/{year_id}/complete-assignment/ "
                        f"pour forcer la transition manuellement."
                    ),
                    academic_year=academic_year,
                )
            except Exception:
                logger.exception(
                    "Unexpected error during complete_assignment for year %s",
                    academic_year.label,
                )
                SystemAlert.objects.create(
                    level="error",
                    title=f"Erreur inattendue après Gale-Shapley — {academic_year.label}",
                    message=(
                        f"L'affectation a été calculée pour {academic_year.label} "
                        f"mais la transition vers Validation a échoué avec une erreur inattendue. "
                        f"Consultez les logs serveur et utilisez l'endpoint "
                        f"/academic/years/{year_id}/complete-assignment/ pour récupérer."
                    ),
                    academic_year=academic_year,
                )

    log_action(
        action="gale_shapley_completed",
        detail=(
            f"Année {academic_year.label} — {assigned}/{len(outputs)} affecté(s)"
            f" — Assignment ID {assignment.id}"
            + (f" — par {triggered_by}" if triggered_by else "")
        ),
    )
