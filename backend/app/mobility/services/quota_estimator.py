from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from app.academic.models import AcademicYear
from app.mobility.models import Agreement, AgreementYear, AgreementYearDepartment

from .agreement_validity import is_within_validity

YEARS_BACK = 5


@dataclass
class InitResult:
    agreements_processed: int = 0
    year_instances_created: int = 0
    department_quotas_created: int = 0
    skipped_existing: int = 0


def initialize_new_year_mobility(new_year: AcademicYear) -> InitResult:
    """
    Pour chaque accord :
      - valid_until >= new_year.start_date (ou pas de date de fin) → is_active = True
      - valid_until < new_year.start_date → is_active = False (visible, activable manuellement)
    Dans les deux cas, copie les données de l'année précédente si disponibles.
    """
    result = InitResult()

    previous_year = (
        AcademicYear.objects.filter(
            status=AcademicYear.CampaignStatus.CLOSED,
            start_date__lt=new_year.start_date,
        )
        .order_by("-start_date")
        .first()
    )

    for agreement in Agreement.objects.prefetch_related("departments").all():
        result.agreements_processed += 1

        # Détermine si l'accord est dans sa période de validité pour cette année
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
        # Crée les quotas par département uniquement si l'accord est actif
        # (pas de répartition pour un accord inactif, sera faite lors de l'activation)
        if auto_active:
            result.department_quotas_created += _create_department_quotas(
                instance, previous_year
            )

    return result


def redistribute_department_quotas(instance: AgreementYear) -> None:
    """Redistribue équitablement n7_places sur les départements contraints."""
    AgreementYearDepartment.objects.filter(agreement_year=instance).delete()
    _create_department_quotas(instance, previous_year=None)


def ensure_dept_quotas_on_activation(instance: AgreementYear) -> None:
    """
    Crée les quotas départements s'ils n'existent pas encore pour cette instance active.
    Appelée lors de l'activation manuelle ou de la mise à jour du quota N7.
    """
    if AgreementYearDepartment.objects.filter(agreement_year=instance).exists():
        return

    if instance.n7_places <= 0:
        return  # Pas de places à distribuer

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


def _estimate_n7_places(
    agreement: Agreement, previous_year: AcademicYear | None
) -> int:
    """
    Priorité :
    1. Valeur de l'année précédente (même accord)
    2. inp_total_places / nombre d'établissements partenaires
    """
    if previous_year is not None:
        prev = AgreementYear.objects.filter(
            agreement=agreement, academic_year=previous_year
        ).first()
        if prev is not None:
            return prev.n7_places

    inp = agreement.inp_total_places
    if inp <= 0:
        return 0

    institutions = [
        i.strip() for i in agreement.inp_institutions.split(",") if i.strip()
    ]
    n_institutions = max(1, len(institutions))
    return max(1, round(inp / n_institutions))


@transaction.atomic
def _create_department_quotas(
    instance: AgreementYear, previous_year: AcademicYear | None
) -> int:
    """
    Priorité :
    1. Proportionnelle aux quotas de l'année précédente (même accord)
    2. Répartition égale sur les départements contraints
    Si aucune contrainte de département définie → tous les départements.
    """
    from app.reference.models import Department as Dept

    constrained = list(instance.agreement.departments.all())
    if not constrained:
        constrained = list(Dept.objects.all().order_by("code"))
    if not constrained:
        return 0

    if previous_year is not None:
        prev_instance = AgreementYear.objects.filter(
            agreement=instance.agreement, academic_year=previous_year
        ).first()
        if prev_instance is not None:
            prev_depts = {
                dq.department_id: dq.estimated_places
                for dq in AgreementYearDepartment.objects.filter(
                    agreement_year=prev_instance
                )
            }
            if prev_depts:
                return _create_from_history(instance, constrained, prev_depts)

    return _create_equal_split(instance, constrained)


def _create_from_history(
    instance: AgreementYear,
    constrained_departments,
    prev_places: dict[int, int],
) -> int:
    constrained_ids = {d.id for d in constrained_departments}
    history_total = sum(v for k, v in prev_places.items() if k in constrained_ids)
    n7 = instance.n7_places

    for department in constrained_departments:
        hist = prev_places.get(department.id, 0)
        if history_total > 0:
            places = round(n7 * hist / history_total)
        else:
            places = n7 // len(constrained_departments)
        AgreementYearDepartment.objects.create(
            agreement_year=instance,
            department=department,
            estimated_places=max(0, places),
        )
    return len(constrained_departments)


def _create_equal_split(instance: AgreementYear, constrained_departments) -> int:
    n = len(constrained_departments)
    if n == 0:
        return 0

    base = instance.n7_places // n
    remainder = instance.n7_places % n

    for i, department in enumerate(constrained_departments):
        AgreementYearDepartment.objects.create(
            agreement_year=instance,
            department=department,
            estimated_places=base + (1 if i < remainder else 0),
        )
    return n


def _ensure_department_quotas(
    instance: AgreementYear, previous_year: AcademicYear | None
) -> None:
    """Crée les quotas départements s'ils n'existent pas encore pour cette instance active."""
    if (
        instance.is_active
        and not AgreementYearDepartment.objects.filter(agreement_year=instance).exists()
    ):
        _create_department_quotas(instance, previous_year)
