from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from app.academic.models import AcademicYear
from app.mobility.models import (
    Agreement,
    AgreementDepartment,
    AgreementYear,
    AgreementYearDepartment,
)

from .agreement_validity import is_within_validity

YEARS_BACK = 5


@dataclass
class InitResult:
    agreements_processed: int = 0
    year_instances_created: int = 0
    department_quotas_created: int = 0
    skipped_existing: int = 0


def initialize_new_year_mobility(new_year: AcademicYear) -> InitResult:
    result = InitResult()

    previous_year = (
        AcademicYear.objects.filter(
            status=AcademicYear.CampaignStatus.CLOSED,
            start_date__lt=new_year.start_date,
        )
        .order_by("-start_date")
        .first()
    )

    for agreement in Agreement.objects.prefetch_related(
        "agreement_departments__department"
    ).all():
        result.agreements_processed += 1

        auto_active = is_within_validity(agreement, new_year)

        instance, created = AgreementYear.objects.get_or_create(
            agreement=agreement,
            academic_year=new_year,
            defaults={
                "is_active": auto_active,
                "n7_places": _estimate_n7_places(agreement, previous_year),
            },
        )

        if not created:
            result.skipped_existing += 1
            _ensure_department_quotas(instance, previous_year)
            continue

        result.year_instances_created += 1
        if auto_active:
            result.department_quotas_created += _create_department_quotas(
                instance, previous_year
            )

    return result


def redistribute_department_quotas(instance: AgreementYear) -> None:
    """Redistribue n7_places sur les départements en conservant les proportions actuelles."""
    current_quotas: dict[int, int] = {
        dq.agreement_department.department_id: dq.get_effective_quota()
        for dq in AgreementYearDepartment.objects.filter(
            agreement_year=instance
        ).select_related("agreement_department")
    }
    AgreementYearDepartment.objects.filter(agreement_year=instance).delete()

    if current_quotas:
        constrained = list(
            AgreementDepartment.objects.filter(
                agreement=instance.agreement
            ).select_related("department")
        )
        if constrained and sum(current_quotas.values()) > 0:
            _create_from_history(instance, constrained, current_quotas)
            return

    _create_department_quotas(instance, previous_year=None)


def ensure_dept_quotas_on_activation(instance: AgreementYear) -> None:
    if AgreementYearDepartment.objects.filter(agreement_year=instance).exists():
        return

    if instance.n7_places <= 0:
        calculated = _estimate_n7_from_inp(instance.agreement)
        if calculated <= 0:
            return
        instance.n7_places = calculated
        instance.save(update_fields=["n7_places", "updated_at"])

    previous_year = (
        AcademicYear.objects.filter(
            status=AcademicYear.CampaignStatus.CLOSED,
            start_date__lt=instance.academic_year.start_date,
        )
        .order_by("-start_date")
        .first()
    )
    _create_department_quotas(instance, previous_year)


# ── private helpers ────────────────────────────────────────────────────────────


def _estimate_n7_from_inp(agreement: Agreement) -> int:
    inp = agreement.inp_total_places
    if inp <= 0:
        return 0
    institutions = [i.strip() for i in agreement.inp_institutions.split(",") if i.strip()]
    n_institutions = max(1, len(institutions))
    return max(1, round(inp / n_institutions))


def _estimate_n7_places(
    agreement: Agreement, previous_year: AcademicYear | None  # noqa: ARG001
) -> int:
    return _estimate_n7_from_inp(agreement)


@transaction.atomic
def _create_department_quotas(
    instance: AgreementYear, previous_year: AcademicYear | None
) -> int:
    from app.reference.models import Department as Dept

    constrained = list(
        AgreementDepartment.objects.filter(agreement=instance.agreement).select_related(
            "department"
        )
    )
    if not constrained:
        all_depts = list(Dept.objects.all().order_by("code"))
        return 0 if not all_depts else _create_equal_split_depts(instance, all_depts)

    if previous_year is not None:
        prev_instance = AgreementYear.objects.filter(
            agreement=instance.agreement, academic_year=previous_year
        ).first()
        if prev_instance is not None:
            prev_depts = {
                dq.agreement_department.department_id: dq.estimated_places
                for dq in AgreementYearDepartment.objects.filter(
                    agreement_year=prev_instance
                ).select_related("agreement_department")
            }
            if prev_depts:
                return _create_from_history(instance, constrained, prev_depts)

    return _create_equal_split(instance, constrained)


def _create_from_history(
    instance: AgreementYear,
    constrained: list[AgreementDepartment],
    prev_places: dict[int, int],
) -> int:
    constrained_dept_ids = {ad.department_id for ad in constrained}
    history_total = sum(v for k, v in prev_places.items() if k in constrained_dept_ids)
    n7 = instance.n7_places
    n = len(constrained)

    if history_total == 0 or n == 0:
        # Fall back to equal split when no usable history.
        return _create_equal_split(instance, constrained)

    # Largest-remainder method: floor each share, then give the remaining
    # places one by one to the departments with the highest fractional parts.
    exact = [
        n7 * prev_places.get(ad.department_id, 0) / history_total for ad in constrained
    ]
    floors = [int(e) for e in exact]
    remainder = n7 - sum(floors)
    fractions = [(exact[i] - floors[i], i) for i in range(n)]
    fractions.sort(key=lambda x: x[0], reverse=True)
    for _, idx in fractions[:remainder]:
        floors[idx] += 1

    for agreement_department, places in zip(constrained, floors, strict=True):
        AgreementYearDepartment.objects.create(
            agreement_year=instance,
            agreement_department=agreement_department,
            estimated_places=max(0, places),
        )
    return n


def _create_equal_split(
    instance: AgreementYear, constrained: list[AgreementDepartment]
) -> int:
    n = len(constrained)
    if n == 0:
        return 0

    base = instance.n7_places // n
    remainder = instance.n7_places % n

    for i, agreement_department in enumerate(constrained):
        AgreementYearDepartment.objects.create(
            agreement_year=instance,
            agreement_department=agreement_department,
            estimated_places=base + (1 if i < remainder else 0),
        )
    return n


def _create_equal_split_depts(instance: AgreementYear, departments) -> int:
    """Fallback : crée des AgreementDepartment à la volée si aucun n'est défini."""
    created_ads = []
    for dept in departments:
        ad, _ = AgreementDepartment.objects.get_or_create(
            agreement=instance.agreement,
            department=dept,
        )
        created_ads.append(ad)
    return _create_equal_split(instance, created_ads)


def _ensure_department_quotas(
    instance: AgreementYear, previous_year: AcademicYear | None
) -> None:
    if (
        instance.is_active
        and not AgreementYearDepartment.objects.filter(agreement_year=instance).exists()
    ):
        _create_department_quotas(instance, previous_year)
