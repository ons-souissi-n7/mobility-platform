from __future__ import annotations

import re
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

    for agreement in Agreement.objects.prefetch_related(
        "agreement_departments__department"
    ).all():
        result.agreements_processed += 1

        auto_active = is_within_validity(agreement, new_year)

        inp = agreement.inp_total_places
        instance, created = AgreementYear.objects.get_or_create(
            agreement=agreement,
            academic_year=new_year,
            defaults={
                "is_active": auto_active,
                "inp_total_places": inp,
                "n7_places": estimate_n7_from_inp(
                    agreement, inp_places=inp, current_year=new_year
                ),
            },
        )

        if not created:
            result.skipped_existing += 1
            _ensure_department_quotas(instance)
            continue

        result.year_instances_created += 1
        if auto_active:
            redistribute_department_quotas(instance)
            result.department_quotas_created += AgreementYearDepartment.objects.filter(
                agreement_year=instance
            ).count()

    return result


@transaction.atomic
def redistribute_department_quotas(instance: AgreementYear) -> None:
    """Redistribue n7_places sur les départements via la méthode Hamilton (US-11).

    Poids : nombre de voeux + affectations par département pour cet accord
    sur les `YEARS_BACK` dernières années universitaires fermées.
    Fallback répartition égale si aucun historique disponible.
    """
    constrained = list(
        AgreementDepartment.objects.filter(agreement=instance.agreement).select_related(
            "department"
        )
    )
    if not constrained:
        _create_department_quotas(instance)
        return

    weights = {ad.department_id: 0 for ad in constrained}
    history = _dept_weights_from_history(instance.agreement, instance.academic_year)
    for dept_id, w in history.items():
        if dept_id in weights:
            weights[dept_id] = w

    AgreementYearDepartment.objects.filter(agreement_year=instance).delete()

    floors = _hamilton(instance.n7_places, weights)
    for ad in constrained:
        AgreementYearDepartment.objects.create(
            agreement_year=instance,
            agreement_department=ad,
            estimated_places=max(0, floors.get(ad.department_id, 0)),
        )


def ensure_dept_quotas_on_activation(instance: AgreementYear) -> None:
    if AgreementYearDepartment.objects.filter(agreement_year=instance).exists():
        return

    if instance.n7_places <= 0:
        inp = instance.inp_total_places or instance.agreement.inp_total_places
        calculated = estimate_n7_from_inp(
            instance.agreement, inp_places=inp, current_year=instance.academic_year
        )
        if calculated <= 0:
            return
        instance.n7_places = calculated
        instance.save(update_fields=["n7_places", "updated_at"])

    redistribute_department_quotas(instance)


# ── private helpers ────────────────────────────────────────────────────────────


def _dept_weights_from_history(
    agreement: Agreement, current_year: AcademicYear
) -> dict[int, int]:
    """Calcule les poids par département à partir de l'historique des voeux
    et des affectations sur les `YEARS_BACK` dernières années fermées.

    1. On cherche d'abord l'historique de l'accord lui-même.
    2. Si aucun historique propre (accord nouveau ou extension), on agrège
       l'historique de tous les accords avec la même université partenaire :
       un nouvel accord est traité comme une extension de l'existant.
    """
    from django.db.models import Count

    from app.outgoing.models import AssignmentResult
    from app.students.models import StudentWish

    past_years = list(
        AcademicYear.objects.filter(
            status=AcademicYear.CampaignStatus.CLOSED,
            start_date__lt=current_year.start_date,
        )
        .order_by("-start_date")
        .values_list("id", flat=True)[:YEARS_BACK]
    )

    if not past_years:
        return {}

    wish_counts: dict[int, int] = dict(
        StudentWish.objects.filter(
            agreement_year__agreement=agreement,
            annual_enrollment__academic_year_id__in=past_years,
        )
        .values("annual_enrollment__department_id")
        .annotate(n=Count("id"))
        .values_list("annual_enrollment__department_id", "n")
    )

    assign_counts: dict[int, int] = dict(
        AssignmentResult.objects.filter(
            agreement_year__agreement=agreement,
            assignment__academic_year_id__in=past_years,
        )
        .values("annual_enrollment__department_id")
        .annotate(n=Count("id"))
        .values_list("annual_enrollment__department_id", "n")
    )

    # Aucun historique propre → accord nouveau ou extension : on utilise
    # l'historique agrégé de tous les accords avec la même université partenaire.
    if not wish_counts and not assign_counts:
        wish_counts = dict(
            StudentWish.objects.filter(
                agreement_year__agreement__partner_university=agreement.partner_university,
                annual_enrollment__academic_year_id__in=past_years,
            )
            .values("annual_enrollment__department_id")
            .annotate(n=Count("id"))
            .values_list("annual_enrollment__department_id", "n")
        )
        assign_counts = dict(
            AssignmentResult.objects.filter(
                agreement_year__agreement__partner_university=agreement.partner_university,
                assignment__academic_year_id__in=past_years,
            )
            .values("annual_enrollment__department_id")
            .annotate(n=Count("id"))
            .values_list("annual_enrollment__department_id", "n")
        )

    all_dept_ids = set(wish_counts) | set(assign_counts)
    return {
        dept_id: wish_counts.get(dept_id, 0) + assign_counts.get(dept_id, 0)
        for dept_id in all_dept_ids
    }


def _hamilton(total: int, weights: dict[int, int]) -> dict[int, int]:
    """Distribue `total` entier entre les clés de `weights` par la méthode Hamilton
    (plus grands restes). Garantit que la somme des résultats == total.

    Si tous les poids sont nuls, applique une répartition égale.
    """
    keys = list(weights.keys())
    if not keys or total <= 0:
        return dict.fromkeys(keys, 0)

    weight_total = sum(weights.values())
    if weight_total == 0:
        # Répartition égale en cas d'absence de données de pondération
        base, rem = divmod(total, len(keys))
        return {k: base + (1 if i < rem else 0) for i, k in enumerate(keys)}

    exact = {k: total * weights[k] / weight_total for k in keys}
    floors = {k: int(v) for k, v in exact.items()}
    remainder = total - sum(floors.values())
    by_fraction = sorted(keys, key=lambda k: exact[k] - floors[k], reverse=True)
    for k in by_fraction[:remainder]:
        floors[k] += 1
    return floors


_N7_ALIASES = frozenset({"n7", "enseeiht", "inp-enseeiht", "inp enseeiht"})


def _institutions_include_n7(institutions: list[str]) -> bool:
    return any(i.lower() in _N7_ALIASES for i in institutions)


def estimate_n7_from_inp(
    agreement: Agreement,
    inp_places: int | None = None,
    current_year: AcademicYear | None = None,
) -> int:
    """Calcule le quota N7 à partir du total INP.

    Priorité :
    1. Si N7 est le seul établissement (inp_institutions vide ou = N7 seul) → 100 % des places.
    2. Ratio N7/INP historique de cet accord (années fermées).
    3. Ratio N7/INP historique de tous les accords avec la même université partenaire.
    4. Division égale entre les établissements INP (inp / n_institutions).
    """
    inp = inp_places if inp_places is not None else agreement.inp_total_places
    if inp <= 0:
        return 0

    # Accepte , ; | comme séparateurs (identique au parser frontend).
    institutions = [
        i.strip() for i in re.split(r"[,;|]", agreement.inp_institutions) if i.strip()
    ]
    other_institutions = [i for i in institutions if i.lower() not in _N7_ALIASES]

    # Si N7 est le seul établissement, il reçoit toutes les places INP.
    if not other_institutions:
        return inp

    if current_year is not None:
        ratio = _n7_inp_ratio_from_history(agreement, current_year)
        # Un ratio = 1.0 avec d'autres établissements présents signale des données
        # historiques incorrectes (N7 avait toutes les places alors qu'il n'est pas
        # seul). On ignore ce ratio et on tombe sur la division égale.
        if ratio is not None and ratio < 1.0:
            return max(1, round(inp * ratio))

    # Fallback : division égale entre les établissements partageant l'accord.
    # N7 est toujours l'un d'eux — s'il n'est pas explicitement listé on ajoute +1.
    n_institutions = (
        len(institutions)
        if _institutions_include_n7(institutions)
        else len(institutions) + 1
    )
    return max(1, round(inp / max(1, n_institutions)))


def _n7_inp_ratio_from_history(
    agreement: Agreement, current_year: AcademicYear
) -> float | None:
    """Ratio N7/INP pondéré sur les `YEARS_BACK` dernières années fermées.

    Cherche d'abord l'accord lui-même, puis tous les accords de la même
    université partenaire si l'accord n'a pas encore d'historique propre.
    Retourne None si aucune donnée utilisable.
    """
    past_year_ids = list(
        AcademicYear.objects.filter(
            status=AcademicYear.CampaignStatus.CLOSED,
            start_date__lt=current_year.start_date,
        )
        .order_by("-start_date")
        .values_list("id", flat=True)[:YEARS_BACK]
    )
    if not past_year_ids:
        return None

    rows = list(
        AgreementYear.objects.filter(
            agreement=agreement,
            academic_year_id__in=past_year_ids,
            inp_total_places__gt=0,
        ).values_list("inp_total_places", "n7_places")
    )

    if not rows:
        rows = list(
            AgreementYear.objects.filter(
                agreement__partner_university=agreement.partner_university,
                academic_year_id__in=past_year_ids,
                inp_total_places__gt=0,
            ).values_list("inp_total_places", "n7_places")
        )

    if not rows:
        return None

    total_inp = sum(r[0] for r in rows)
    total_n7 = sum(r[1] for r in rows)
    return total_n7 / total_inp if total_inp > 0 else None


def _create_department_quotas(instance: AgreementYear) -> None:
    """Fallback quand aucun AgreementDepartment n'est configuré.

    Crée les AgreementDepartment pour tous les départements connus et distribue
    équitablement (Hamilton à poids égaux).
    """
    from app.reference.models import Department as Dept

    all_depts = list(Dept.objects.all().order_by("code"))
    if all_depts:
        _create_equal_split_depts(instance, all_depts)


def _create_equal_split_depts(instance: AgreementYear, departments) -> None:
    """Crée des AgreementDepartment à la volée et distribue équitablement (Hamilton)."""
    created_ads = []
    for dept in departments:
        ad, _ = AgreementDepartment.objects.get_or_create(
            agreement=instance.agreement,
            department=dept,
        )
        created_ads.append(ad)
    equal_weights = {ad.department_id: 1 for ad in created_ads}
    floors = _hamilton(instance.n7_places, equal_weights)
    for ad in created_ads:
        AgreementYearDepartment.objects.create(
            agreement_year=instance,
            agreement_department=ad,
            estimated_places=max(0, floors.get(ad.department_id, 0)),
        )


def _ensure_department_quotas(instance: AgreementYear) -> None:
    if (
        instance.is_active
        and not AgreementYearDepartment.objects.filter(agreement_year=instance).exists()
    ):
        redistribute_department_quotas(instance)
