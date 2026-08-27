"""
Construction du jeu d'entraînement du moteur de recommandation.

Une ligne = un vœu (StudentWish) exprimé lors d'une campagne clôturée.
Cible binaire : l'étudiant a-t-il effectivement été affecté à cette
destination précise (ou une destination du même accord, via une correction
manuelle) ? cf. chapitre 4 du rapport.

Les features reprennent les critères réellement utilisés par l'algorithme
d'affectation Gale-Shapley (cf. `outgoing/services/gale_shapley.py::_score`
et le filtrage par département/quota) : GPA et nationalité pèsent sur la
priorité entre candidats, le département détermine l'éligibilité aux slots
réservés. `historical_rate` complète ces critères par un signal propre au
moteur de recommandation (compétitivité observée de la destination), et
`n7_places` ajoute un signal de capacité indépendant : `historical_rate`
mélange déjà demande et capacité (assignés / vœux), `n7_places` isole la
capacité seule — deux accords avec le même taux historique n'ont pas la
même marge selon qu'ils offrent 1 ou 10 places.
"""

from app.recommendation.services.historical_rate import compute_historical_rates

# [gpa: float, department_code: str, historical_rate: float,
#  is_french: int (0/1), n7_places: int]
FeatureRow = list


def build_training_dataset(
    rates: dict[int, float] | None = None,
) -> tuple[list[FeatureRow], list[int]]:
    """`rates` peut être fourni par l'appelant (déjà calculé pour un autre
    usage dans la même requête) pour éviter de relancer les mêmes agrégats
    SQL — sinon recalculé ici."""
    from app.academic.models import AcademicYear
    from app.outgoing.models import AssignmentResult
    from app.students.models import StudentWish

    if rates is None:
        rates = compute_historical_rates()

    # annual_enrollment_id -> agreement_year_id effectivement retenu (ou None)
    effective_assignment: dict[int, int | None] = {}
    results = AssignmentResult.objects.filter(
        assignment__academic_year__status=AcademicYear.CampaignStatus.CLOSED
    ).only("annual_enrollment_id", "agreement_year_id", "override_agreement_year_id")
    for r in results:
        effective_assignment[r.annual_enrollment_id] = (
            r.override_agreement_year_id or r.agreement_year_id
        )

    wishes = StudentWish.objects.filter(
        annual_enrollment__academic_year__status=AcademicYear.CampaignStatus.CLOSED
    ).select_related(
        "annual_enrollment__department",
        "annual_enrollment__student__nationality",
        "agreement_year",
    )

    rows: list[FeatureRow] = []
    targets: list[int] = []
    for wish in wishes:
        enrollment = wish.annual_enrollment
        gpa = float(enrollment.gpa) if enrollment.gpa is not None else 0.0
        dept_code = enrollment.department.code
        rate = rates.get(wish.agreement_year.agreement_id, 0.0)
        nationality = enrollment.student.nationality
        is_french = 1 if nationality is not None and nationality.iso2 == "FR" else 0
        n7_places = wish.agreement_year.n7_places or 0
        rows.append([gpa, dept_code, rate, is_french, n7_places])

        assigned_to = effective_assignment.get(enrollment.id)
        targets.append(1 if assigned_to == wish.agreement_year_id else 0)

    return rows, targets
