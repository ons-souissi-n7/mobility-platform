from django.db import transaction

from app.academic.models import AcademicYear
from app.mobility.models import AgreementYear

from .gale_shapley import AgreementInput, StudentInput, gale_shapley


def run_gale_shapley(year_id: int, triggered_by: str = "") -> None:
    from app.outgoing.models import Assignment, AssignmentResult
    from app.students.models import AnnualEnrollment, StudentWish

    try:
        academic_year = AcademicYear.objects.get(pk=year_id)
    except AcademicYear.DoesNotExist as exc:
        raise ValueError(f"Année académique {year_id} introuvable.") from exc

    # ── Charger les étudiants et leurs vœux ──────────────────────────────
    enrollments = AnnualEnrollment.objects.filter(
        academic_year=academic_year
    ).select_related("student__nationality", "department")

    wishes_qs = (
        StudentWish.objects.filter(
            annual_enrollment__academic_year=academic_year,
        )
        .select_related("annual_enrollment")
        .order_by("annual_enrollment_id", "rank")
    )

    wishes_by_enrollment: dict[int, list[int]] = {}
    for wish in wishes_qs:
        eid = wish.annual_enrollment_id
        wishes_by_enrollment.setdefault(eid, []).append(wish.agreement_year_id)

    student_inputs: list[StudentInput] = []
    for enrollment in enrollments:
        prefs = wishes_by_enrollment.get(enrollment.id, [])
        if not prefs:
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
            )
        )

    # ── Charger les accords actifs pour cette année ───────────────────────
    agreement_years = AgreementYear.objects.filter(
        academic_year=academic_year,
        is_active=True,
        n7_places__gt=0,
    ).prefetch_related("department_quotas__agreement_department__department")

    agreement_inputs: list[AgreementInput] = []
    for ay in agreement_years:
        quota_dept: dict[int, int] = {}
        for dq in ay.department_quotas.all():
            dept_id = dq.agreement_department.department_id
            quota_dept[dept_id] = dq.get_effective_quota()
        agreement_inputs.append(
            AgreementInput(
                agreement_year_id=ay.id,
                n7_places=ay.n7_places,
                quota_dept=quota_dept,
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
                )
                for output in outputs
            ]
        )
