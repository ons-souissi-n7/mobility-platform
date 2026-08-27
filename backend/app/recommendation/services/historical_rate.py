"""
Taux d'affectation historique par accord (Agreement) — cf. chapitre 4 du
rapport (feature "taux historique d'affectation" du moteur de recommandation).

La clé est l'Agreement (le partenariat, stable d'une année sur l'autre), pas
l'AgreementYear (une instance par campagne) : le taux doit rester utilisable
pour scorer les AgreementYear de la campagne en cours, qui n'existaient pas
encore lors des campagnes closes sur lesquelles il est calculé.
"""

from django.db.models import Count


def compute_historical_rates() -> dict[int, float]:
    """agreement_id -> part des vœux (sur les campagnes clôturées) qui se
    sont soldés par une affectation vers ce même accord.

    La destination effective d'un résultat est `override_agreement_year` si
    renseigné, sinon `agreement_year` (même règle que le calcul de la cible
    dans build_training_dataset() — une correction manuelle qui affecte un
    étudiant "non affecté" vers un accord doit compter comme une affectation
    ici aussi, sous peine d'entraîner le modèle avec une feature qui
    contredit sa propre cible pour les mêmes lignes)."""
    from app.academic.models import AcademicYear
    from app.outgoing.models import AssignmentResult
    from app.students.models import StudentWish

    wish_counts: dict[int, int] = {
        row["agreement_year__agreement_id"]: row["n"]
        for row in (
            StudentWish.objects.filter(
                annual_enrollment__academic_year__status=(
                    AcademicYear.CampaignStatus.CLOSED
                )
            )
            .values("agreement_year__agreement_id")
            .annotate(n=Count("id"))
        )
    }

    assigned_counts: dict[int, int] = {}
    results = AssignmentResult.objects.filter(
        assignment__academic_year__status=AcademicYear.CampaignStatus.CLOSED,
    ).select_related("agreement_year", "override_agreement_year")
    for r in results:
        effective_ay = r.override_agreement_year or r.agreement_year
        if effective_ay is None:
            continue
        assigned_counts[effective_ay.agreement_id] = (
            assigned_counts.get(effective_ay.agreement_id, 0) + 1
        )

    return {
        agreement_id: assigned_counts.get(agreement_id, 0) / wished
        for agreement_id, wished in wish_counts.items()
        if wished
    }
