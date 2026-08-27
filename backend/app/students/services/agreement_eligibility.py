"""
Filtrage des AgreementYear éligibles pour le profil d'un étudiant (niveau,
département) — utilisé à la fois par le portail étudiant (accords proposés,
recommandations) pour éviter que les deux endpoints ne divergent au fil du
temps sur ce qui compte comme "éligible".
"""

from app.mobility.models import AgreementYear
from app.shared.excel_utils import format_university_label


def eligible_agreement_years(enrollment, year_id: int) -> list[AgreementYear]:
    """AgreementYear actives de l'année, filtrées par niveau/département de
    l'inscription. Sans inscription, retourne tout (comportement historique
    de get_student_agreements quand l'étudiant n'a pas d'inscription pour
    l'année demandée)."""
    ays = (
        AgreementYear.objects.filter(
            academic_year_id=year_id, is_active=True, n7_places__gt=0
        )
        .select_related("agreement__partner_university__country")
        .prefetch_related(
            "department_quotas__agreement_department__department",
            "agreement__levels",
            "agreement__agreement_departments",
        )
    )
    if enrollment is None:
        return list(ays)

    result = []
    for ay in ays:
        agreement = ay.agreement
        # `.level_ids` / `.agreement_departments.all()` lisent le cache de
        # prefetch_related ci-dessus (contrairement à `.values_list()`/
        # `.filter()`, qui rééxécutent une requête et l'annulent).
        level_ids = agreement.level_ids
        if level_ids and enrollment.level_id not in level_ids:
            continue
        dept_ids = [ad.department_id for ad in agreement.agreement_departments.all()]
        if dept_ids and enrollment.department_id not in dept_ids:
            continue
        result.append(ay)
    return result


def partner_university_display(univ) -> tuple[str, str, str]:
    """(nom_affiché, nom_pays, code_iso2_pays) pour une PartnerUniversity."""
    country_name = univ.country.name_fr if univ.country_id else ""
    country_iso2 = univ.country.iso2 if univ.country_id else ""
    label = format_university_label(univ.name, univ.short_name or "", country_name)
    return label, country_name, country_iso2
