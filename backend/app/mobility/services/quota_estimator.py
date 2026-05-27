from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from statistics import mean

from django.db import transaction
from django.db.models import Q

from app.academic.models import AcademicYear
from app.mobility.models import (
    Agreement,
    AgreementDepartmentConstraint,
    AgreementQuota,
    AgreementYearAvailability,
    DepartmentQuota,
)
from app.reference.models import Department

from .agreement_validity import is_agreement_valid_for_year

DEFAULT_INP_TO_N7_RATIO = 1 / 3
DEFAULT_ESTIMATED_PLACES = 1
ESTIMATION_PERIOD = "Annuel"
YEARS_BACK = 5


@dataclass
class EstimationResult:
    eligible_agreements: int = 0
    quota_created: int = 0
    department_quota_created: int = 0
    skipped_existing_quota: int = 0
    skipped_no_current_year: int = 0


def initialize_new_year_mobility(new_year: AcademicYear) -> EstimationResult:
    previous_year = (
        AcademicYear.objects.filter(status=AcademicYear.CampaignStatus.CLOSED)
        .order_by("-closed_at", "-start_date")
        .first()
    )
    if previous_year:
        prev_availability_map = {
            av.agreement_id: av.is_available
            for av in AgreementYearAvailability.objects.filter(
                academic_year_label=previous_year.label
            )
        }
        for agreement in Agreement.objects.select_related("partner_university").all():
            if not is_agreement_valid_for_year(agreement, previous_year):
                continue
            was_available = prev_availability_map.get(agreement.id, True)
            AgreementYearAvailability.objects.get_or_create(
                agreement=agreement,
                academic_year_label=new_year.label,
                defaults={
                    "academic_year": new_year,
                    "is_available": was_available,
                    "source": "auto_initialized",
                    "remarks": "",
                },
            )
    return estimate_current_year_missing_quotas(year=new_year)


def estimate_current_year_missing_quotas(
    year: AcademicYear | None = None,
) -> EstimationResult:
    current_year = year or AcademicYear.get_current()
    result = EstimationResult()

    if current_year is None:
        result.skipped_no_current_year = 1
        return result

    for agreement in Agreement.objects.select_related("partner_university").all():
        if not is_agreement_valid_for_year(agreement, current_year):
            continue

        result.eligible_agreements += 1

        if AgreementQuota.objects.filter(
            agreement=agreement,
            academic_year_label=current_year.label,
        ).exists():
            result.skipped_existing_quota += 1
            for quota in AgreementQuota.objects.filter(
                agreement=agreement,
                academic_year_label=current_year.label,
                department_quotas__isnull=True,
            ):
                result.department_quota_created += create_estimated_department_quotas(
                    agreement,
                    quota,
                    current_year,
                )
            continue

        quota = create_estimated_agreement_quota(agreement, current_year)
        result.quota_created += 1
        result.department_quota_created += create_estimated_department_quotas(
            agreement,
            quota,
            current_year,
        )

    return result


@transaction.atomic
def create_estimated_agreement_quota(
    agreement: Agreement,
    current_year: AcademicYear,
) -> AgreementQuota:
    historical_quotas = get_historical_quotas(agreement, current_year)
    has_history = bool(historical_quotas)
    total_places = estimate_total_places(historical_quotas)
    period = estimate_period(historical_quotas)
    total_duration = estimate_optional_int(
        [quota.total_duration for quota in historical_quotas if quota.total_duration]
    )
    duration_unit = estimate_text([quota.duration_unit for quota in historical_quotas])

    return AgreementQuota.objects.create(
        agreement=agreement,
        academic_year=current_year,
        academic_year_label=current_year.label,
        period=period,
        source_scope="estimated_from_history" if has_history else "manual_required",
        total_places=total_places,
        remaining_places=total_places,
        estimated_total_places=total_places,
        total_duration=total_duration,
        duration_unit=duration_unit,
        is_effective=True,
        is_estimated=True,
        estimation_basis=get_estimation_basis(historical_quotas),
        remarks="",
    )


def create_estimated_department_quotas(
    agreement: Agreement,
    quota: AgreementQuota,
    current_year: AcademicYear | None,
) -> int:
    constrained_departments = get_active_constraint_departments(agreement)
    if current_year is None:
        return create_inferred_department_quotas(
            agreement,
            quota,
            constrained_departments,
        )

    cutoff = get_cutoff_date(current_year)
    current_start_year = current_year.start_date.year

    by_fk = Q(
        agreement_quota__academic_year__start_date__gte=cutoff,
        agreement_quota__academic_year__start_date__lt=current_year.start_date,
    )
    label_q = Q()
    for year in range(cutoff.year, current_start_year):
        label_q |= Q(
            agreement_quota__academic_year__isnull=True,
            agreement_quota__academic_year_label__startswith=str(year),
        )

    historical_department_quotas = list(
        DepartmentQuota.objects.filter(agreement_quota__agreement=agreement)
        .filter(by_fk | label_q)
        .distinct()
        .select_related("department", "agreement_quota")
    )

    places_by_department: dict[int, list[int]] = defaultdict(list)
    for department_quota in historical_department_quotas:
        places_by_department[department_quota.department_id].append(
            department_quota.places
        )

    if not places_by_department:
        return create_inferred_department_quotas(
            agreement, quota, constrained_departments
        )

    created = 0
    for department_id, places_values in places_by_department.items():
        if constrained_departments and department_id not in {
            department.id for department in constrained_departments
        }:
            continue
        estimated_places = max(0, round(mean(places_values)))
        if estimated_places == 0:
            continue

        DepartmentQuota.objects.create(
            agreement_quota=quota,
            department_id=department_id,
            places=estimated_places,
            estimated_places=estimated_places,
            is_estimated=True,
            estimation_basis=(
                f"Moyenne des quotas departement sur {len(places_values)} valeur(s) "
                f"des {YEARS_BACK} dernieres annees."
            ),
            remarks="",
        )
        created += 1

    return created


def estimate_n7_places_from_inp_quota(
    agreement: Agreement,
    current_year: AcademicYear | None,
    inp_total_places: int,
) -> tuple[int, str]:
    if inp_total_places <= 0:
        return (
            DEFAULT_ESTIMATED_PLACES,
            "Quota INP MoveON absent ou nul; valeur minimale proposee.",
        )

    ratio_info = get_best_historical_ratio(
        agreement=agreement,
        current_year=current_year,
    )

    if ratio_info is not None:
        ratio, sample_count, basis = ratio_info
        return (
            max(1, min(inp_total_places, round(inp_total_places * ratio))),
            (
                "Quota N7 estime depuis le quota INP MoveON avec ratio historique N7/INP "
                f"moyen {ratio:.2f} sur {sample_count} valeur(s) ({basis})."
            ),
        )

    estimated = max(1, round(inp_total_places * DEFAULT_INP_TO_N7_RATIO))
    return (
        min(inp_total_places, estimated),
        (
            "Quota N7 estime a partir du quota INP MoveON avec ratio par defaut 1/3 "
            f"({get_agreement_category_label(agreement)}, direction={agreement.direction})."
        ),
    )


def get_best_historical_ratio(
    *,
    agreement: Agreement,
    current_year: AcademicYear | None,
) -> tuple[float, int, str] | None:
    """
    Choisit la meilleure base de ratio historique N7/INP.
    Priorite:
    1) historique du meme accord
    2) historique global sur accords de meme categorie+direction
    3) historique global (tous types)
    """

    def ratios_from_quotas(quotas: list[AgreementQuota]) -> list[float]:
        values: list[float] = []
        for quota in quotas:
            if (
                quota.source_total_places
                and quota.source_total_places > 0
                and quota.total_places > 0
            ):
                values.append(quota.total_places / quota.source_total_places)
        return values

    historical_quotas = (
        get_historical_quotas(agreement, current_year)
        if current_year is not None
        else list(AgreementQuota.objects.filter(agreement=agreement))
    )
    agreement_ratios = ratios_from_quotas(historical_quotas)
    if agreement_ratios:
        return (
            mean(agreement_ratios),
            len(agreement_ratios),
            f"accord={agreement.id}, {get_agreement_category_label(agreement)}, direction={agreement.direction}",
        )

    # Pool by category+direction (across agreements)
    pool_queryset = AgreementQuota.objects.select_related(
        "agreement", "academic_year"
    ).filter(
        agreement__framework_ref_id=agreement.framework_ref_id,
        agreement__direction=agreement.direction,
    )
    if current_year is not None:
        pool_queryset = pool_queryset.filter(
            academic_year__start_date__gte=get_cutoff_date(current_year),
            academic_year__start_date__lt=current_year.start_date,
        )

    pool_ratios = ratios_from_quotas(list(pool_queryset))
    if pool_ratios:
        return (
            mean(pool_ratios),
            len(pool_ratios),
            f"{get_agreement_category_label(agreement)}, direction={agreement.direction}",
        )

    # Global fallback pool
    global_queryset = AgreementQuota.objects.select_related(
        "agreement", "academic_year"
    ).all()
    if current_year is not None:
        global_queryset = global_queryset.filter(
            academic_year__start_date__gte=get_cutoff_date(current_year),
            academic_year__start_date__lt=current_year.start_date,
        )
    global_ratios = ratios_from_quotas(list(global_queryset))
    if global_ratios:
        return (mean(global_ratios), len(global_ratios), "global")

    return None


def get_agreement_category_label(agreement: Agreement) -> str:
    if agreement.framework_ref_id and agreement.framework_ref:
        return f"categorie={agreement.framework_ref.name}"
    if agreement.framework:
        return f"categorie={agreement.framework}"
    return "categorie=non renseignee"


def create_inferred_department_quotas(
    agreement: Agreement,
    quota: AgreementQuota,
    constrained_departments: list[Department] | None = None,
) -> int:
    departments = constrained_departments or list(
        Department.objects.all().order_by("code")
    )
    if not departments:
        return 0

    base = quota.total_places // len(departments)
    remainder = quota.total_places % len(departments)
    created = 0

    for index, department in enumerate(departments):
        places = base + (1 if index < remainder else 0)
        if places < 0:
            continue

        DepartmentQuota.objects.create(
            agreement_quota=quota,
            department=department,
            places=places,
            estimated_places=places,
            is_estimated=True,
            estimation_basis=(
                "Repartition egale sur les departements explicitement concernes par l'accord."
                if constrained_departments
                else "Repartition egale sur tous les departements (aucune contrainte definie)."
            ),
            remarks="",
        )
        created += 1

    return created


def get_active_constraint_departments(agreement: Agreement) -> list[Department]:
    constraints = AgreementDepartmentConstraint.objects.filter(
        agreement=agreement,
        is_active=True,
    ).select_related("department")
    return [constraint.department for constraint in constraints]


def infer_departments_for_agreement(agreement: Agreement) -> list[Department]:
    text = " ".join(
        [
            agreement.formation,
            agreement.discipline,
            agreement.isced,
            agreement.name,
            agreement.remarks,
            agreement.restrictions,
        ],
    ).lower()
    departments = list(Department.objects.all().order_by("code"))
    matched = []

    keyword_by_code = {
        "SN": [
            "informatique",
            "math",
            "numerique",
            "numérique",
            "computer",
            "ict",
            "061",
        ],
        "3EA": [
            "electronique",
            "électronique",
            "electric",
            "electrical",
            "autom",
            "0713",
            "0714",
        ],
        "MF2E": ["mecanique", "mécanique", "fluide", "hydraulique", "mechanic", "0715"],
        "HYD": ["hydraulique", "fluide", "water"],
        "TR": ["telecom", "télécom", "reseaux", "réseaux", "network"],
    }

    for department in departments:
        code = department.code.upper()
        keywords = keyword_by_code.get(
            code, [department.code.lower(), department.name.lower()]
        )
        if any(keyword in text for keyword in keywords):
            matched.append(department)

    return matched


def get_historical_quotas(
    agreement: Agreement,
    current_year: AcademicYear | None,
) -> list[AgreementQuota]:
    if current_year is None:
        return list(AgreementQuota.objects.filter(agreement=agreement))

    cutoff = get_cutoff_date(current_year)
    current_start_year = current_year.start_date.year

    # Quotas whose academic_year FK is properly linked and in range
    by_fk = Q(
        academic_year__start_date__gte=cutoff,
        academic_year__start_date__lt=current_year.start_date,
    )

    # Fallback: quotas without a linked academic_year but whose label year is in range
    # Labels follow the format "YYYY-YYYY" (e.g. "2024-2025")
    label_q = Q()
    for year in range(cutoff.year, current_start_year):
        label_q |= Q(
            academic_year__isnull=True, academic_year_label__startswith=str(year)
        )

    return list(
        AgreementQuota.objects.filter(agreement=agreement)
        .filter(by_fk | label_q)
        .distinct()
        .order_by("-academic_year_label")
    )


def get_cutoff_date(current_year: AcademicYear) -> date:
    return date(
        current_year.start_date.year - YEARS_BACK,
        current_year.start_date.month,
        current_year.start_date.day,
    )


def estimate_total_places(historical_quotas: list[AgreementQuota]) -> int:
    values = [
        quota.total_places for quota in historical_quotas if quota.total_places > 0
    ]
    if not values:
        return 0

    return max(1, round(mean(values)))


def estimate_period(historical_quotas: list[AgreementQuota]) -> str:
    return (
        estimate_text([quota.period for quota in historical_quotas])
        or ESTIMATION_PERIOD
    )


def estimate_text(values: list[str]) -> str:
    cleaned_values = [value for value in values if value]
    if not cleaned_values:
        return ""

    return Counter(cleaned_values).most_common(1)[0][0]


def estimate_optional_int(values: list[int]) -> int | None:
    if not values:
        return None

    return max(0, round(mean(values)))


def get_estimation_basis(historical_quotas: list[AgreementQuota]) -> str:
    if not historical_quotas:
        return (
            "Aucun quota historique disponible sur les 5 dernieres annees; "
            "saisie manuelle requise."
        )

    return (
        f"Moyenne basee sur {len(historical_quotas)} quota(s) des "
        f"{YEARS_BACK} dernieres annees."
    )


def normalize_year_label(label: str) -> str:
    # Backward-compatible wrapper for older imports.
    # New code should use agreement_validity.normalize_year_label.
    return label.replace("/", "-").strip()
