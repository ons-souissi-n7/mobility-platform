from ninja import Router
from ninja.errors import HttpError

from app.academic.models import AcademicYear
from app.auth.permissions import require_student_owns
from app.outgoing.models import AssignmentResult, AssignmentStatus, SlotType
from app.recommendation.services.historical_rate import compute_historical_rates
from app.recommendation.services.model import score_destinations, train_model
from app.shared.excel_utils import format_university_label
from app.students.models import AnnualEnrollment, Student, StudentWish
from app.students.services.agreement_eligibility import (
    eligible_agreement_years,
    partner_university_display,
)

from .schemas import (
    EnrolledYearOut,
    StudentAgreementDeptQuotaOut,
    StudentAgreementOut,
    StudentAssignmentOut,
    StudentProfileOut,
    StudentRecommendationOut,
    StudentWishItemOut,
)

router = Router()

STUDENT_NOT_FOUND = "Étudiant introuvable."


@router.get(
    "/{ine}/profile/",
    response=StudentProfileOut,
    summary="Profil étudiant et années d'inscription",
)
@require_student_owns()
def get_student_profile(request, ine: str):
    try:
        student = Student.objects.get(ine=ine)
    except Student.DoesNotExist as exc:
        raise HttpError(404, STUDENT_NOT_FOUND) from exc

    enrollments = (
        AnnualEnrollment.objects.filter(student=student)
        .select_related("academic_year")
        .order_by("-academic_year__start_date")
    )
    enrolled_years = [
        EnrolledYearOut(
            academic_year_id=e.academic_year_id,
            academic_year_label=e.academic_year.label,
            academic_year_status=e.academic_year.status,
        )
        for e in enrollments
    ]
    return StudentProfileOut(
        ine=student.ine,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        enrolled_years=enrolled_years,
    )


@router.get(
    "/{ine}/agreements/",
    response=list[StudentAgreementOut],
    summary="Accords éligibles au profil de l'étudiant",
)
@require_student_owns()
def get_student_agreements(request, ine: str, year_id: int | None = None):
    try:
        student = Student.objects.get(ine=ine)
    except Student.DoesNotExist as exc:
        raise HttpError(404, STUDENT_NOT_FOUND) from exc

    if year_id:
        try:
            AcademicYear.objects.get(pk=year_id)
        except AcademicYear.DoesNotExist as exc:
            raise HttpError(404, "Année académique introuvable.") from exc
    else:
        enrollment_latest = (
            AnnualEnrollment.objects.filter(student=student)
            .select_related("academic_year")
            .order_by("-academic_year__start_date")
            .first()
        )
        if not enrollment_latest:
            return []
        year_id = enrollment_latest.academic_year_id

    enrollment = (
        AnnualEnrollment.objects.filter(student=student, academic_year_id=year_id)
        .select_related("department", "level")
        .first()
    )

    result = []
    for ay in eligible_agreement_years(enrollment, year_id):
        a = ay.agreement
        univ = a.partner_university
        university_name, country_name, country_iso2 = partner_university_display(univ)
        dept_quotas = [
            StudentAgreementDeptQuotaOut(
                department_id=dq.agreement_department.department_id,
                department_code=dq.agreement_department.department.code,
                effective_places=dq.get_effective_quota(),
            )
            for dq in ay.department_quotas.all()
        ]
        result.append(
            StudentAgreementOut(
                agreement_year_id=ay.id,
                agreement_id=a.id,
                agreement_name=a.name,
                university_name=university_name,
                country_name=country_name,
                country_iso2=country_iso2,
                n7_places=ay.n7_places,
                dept_quotas=dept_quotas,
                valid_from=a.valid_from,
                valid_until=a.valid_until,
                direction=a.direction,
            )
        )
    return result


@router.get(
    "/{ine}/wishes/",
    response=list[StudentWishItemOut],
    summary="Vœux de l'étudiant pour une année",
)
@require_student_owns()
def get_student_wishes(request, ine: str, year_id: int | None = None):
    try:
        student = Student.objects.get(ine=ine)
    except Student.DoesNotExist as exc:
        raise HttpError(404, STUDENT_NOT_FOUND) from exc

    filters: dict = {"student": student}
    if year_id:
        filters["academic_year_id"] = year_id

    enrollment = (
        AnnualEnrollment.objects.filter(**filters)
        .order_by("-academic_year__start_date")
        .first()
    )
    if not enrollment:
        return []

    wishes = (
        StudentWish.objects.filter(annual_enrollment=enrollment)
        .select_related("agreement_year__agreement__partner_university__country")
        .order_by("rank")
    )
    return [
        StudentWishItemOut(
            rank=w.rank,
            agreement_year_id=w.agreement_year_id,
            agreement_name=w.agreement_year.agreement.name,
            university_name=w.agreement_year.agreement.partner_university.name,
            country_name=(
                w.agreement_year.agreement.partner_university.country.name_fr
                if w.agreement_year.agreement.partner_university.country_id
                else ""
            ),
            country_iso2=(
                w.agreement_year.agreement.partner_university.country.iso2
                if w.agreement_year.agreement.partner_university.country_id
                else ""
            ),
        )
        for w in wishes
    ]


@router.get(
    "/{ine}/recommendations/",
    response=list[StudentRecommendationOut],
    summary="Destinations recommandées avant la saisie des vœux",
)
@require_student_owns()
def get_student_recommendations(request, ine: str, year_id: int | None = None):
    try:
        student = Student.objects.get(ine=ine)
    except Student.DoesNotExist as exc:
        raise HttpError(404, STUDENT_NOT_FOUND) from exc

    if year_id:
        try:
            AcademicYear.objects.get(pk=year_id)
        except AcademicYear.DoesNotExist as exc:
            raise HttpError(404, "Année académique introuvable.") from exc
    else:
        enrollment_latest = (
            AnnualEnrollment.objects.filter(student=student)
            .order_by("-academic_year__start_date")
            .first()
        )
        if not enrollment_latest:
            return []
        year_id = enrollment_latest.academic_year_id

    enrollment = (
        AnnualEnrollment.objects.filter(student=student, academic_year_id=year_id)
        .select_related("department", "level", "student__nationality")
        .first()
    )
    if not enrollment:
        return []

    eligible = eligible_agreement_years(enrollment, year_id)
    if not eligible:
        return []

    # Calculé une seule fois ici et réutilisé pour l'entraînement : sans ça,
    # train_model() -> build_training_dataset() relance la même agrégation.
    rates = compute_historical_rates()
    pipeline = train_model(rates=rates)
    nationality = enrollment.student.nationality
    is_french = nationality is not None and nationality.iso2 == "FR"
    scores = score_destinations(
        gpa=enrollment.gpa,
        department_code=enrollment.department.code,
        agreement_ids=[ay.agreement_id for ay in eligible],
        pipeline=pipeline,
        rates=rates,
        is_french=is_french,
    )

    # Sans modèle entraîné (démarrage à froid, cf. chapitre 4 du rapport),
    # `scores` vaut [None, ...] pour tous : le seul signal par destination
    # encore disponible est son taux historique (le GPA du candidat, lui,
    # est constant sur toute la liste et ne peut pas servir de clé de tri).
    model_based = pipeline is not None
    ranked = sorted(
        zip(eligible, scores, strict=True),
        key=lambda pair: (
            pair[1] if pair[1] is not None else rates.get(pair[0].agreement_id, 0.0)
        ),
        reverse=True,
    )

    result = []
    for ay, score in ranked:
        a = ay.agreement
        univ = a.partner_university
        university_name, country_name, country_iso2 = partner_university_display(univ)
        result.append(
            StudentRecommendationOut(
                agreement_year_id=ay.id,
                agreement_name=a.name,
                university_name=university_name,
                country_name=country_name,
                country_iso2=country_iso2,
                score=score,
                model_based=model_based,
            )
        )
    return result


@router.get(
    "/{ine}/assignment/",
    response=StudentAssignmentOut,
    summary="Résultat d'affectation d'un étudiant",
)
@require_student_owns()
def get_student_assignment(request, ine: str, year_id: int | None = None):
    filters: dict = {
        "annual_enrollment__student__ine": ine,
        "assignment__status": AssignmentStatus.PUBLISHED,
    }
    if year_id:
        filters["assignment__academic_year_id"] = year_id

    result = (
        AssignmentResult.objects.filter(**filters)
        .select_related(
            "agreement_year__agreement__partner_university__country",
            "override_agreement_year__agreement__partner_university__country",
        )
        .order_by("-assignment__created_at")
        .first()
    )

    if result is None:
        raise HttpError(404, "Aucun résultat publié pour cet étudiant.")

    is_assigned = (
        result.slot_type != SlotType.UNASSIGNED
        or result.override_agreement_year_id is not None
    )

    if is_assigned:
        effective_ay = result.override_agreement_year or result.agreement_year
        if effective_ay:
            univ = effective_ay.agreement.partner_university
            university_name = format_university_label(
                univ.name,
                univ.short_name or "",
                univ.country.name_fr if univ.country_id else "",
            )
            country_name = univ.country.name_fr if univ.country_id else None
            agreement_name = effective_ay.agreement.name
        else:
            university_name = None
            country_name = None
            agreement_name = None
    else:
        university_name = None
        country_name = None
        agreement_name = None

    effective_rank = (
        result.override_rank if result.source == "override" else result.assigned_rank
    )

    return StudentAssignmentOut(
        is_assigned=is_assigned,
        slot_type=result.slot_type,
        university_name=university_name,
        country_name=country_name,
        agreement_name=agreement_name,
        effective_rank=effective_rank,
        override_reason=result.override_reason or None,
    )
