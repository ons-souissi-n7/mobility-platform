from decimal import ROUND_HALF_UP, Decimal


def _weeks_from_dates(start_date, end_date) -> Decimal:
    if not start_date or not end_date:
        return Decimal("0")
    days = max((end_date - start_date).days, 0)
    return Decimal(str(days)) / Decimal("7")


def compute_cti_duration(student) -> dict:
    """Calcule la durée de mobilité à la volée (échanges publiés + stages internationaux + complémentaires validées)."""
    from app.complementary.models import ComplementaryMobility
    from app.internships.models import Internship
    from app.outgoing.models import AssignmentResult

    exchange = Decimal("0")
    for result in AssignmentResult.objects.filter(
        annual_enrollment__student=student,
        assignment__status="published",
        agreement_year__isnull=False,
        agreement_year__duration_weeks__isnull=False,
    ).select_related("agreement_year"):
        exchange += Decimal(str(result.agreement_year.duration_weeks))

    internship = Decimal("0")
    for i in (
        Internship.objects.filter(
            student=student,
            weeks_in_company__isnull=False,
        )
        .exclude(country__isnull=True)
        .exclude(country__iso2="FR")
    ):
        internship += Decimal(str(i.weeks_in_company))

    complementary = Decimal("0")
    for m in ComplementaryMobility.objects.filter(student=student, status="validated"):
        complementary += _weeks_from_dates(m.start_date, m.end_date)
    complementary = complementary.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    total = (exchange + internship + complementary).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )

    return {
        "exchange_weeks": float(exchange),
        "internship_weeks": float(internship),
        "complementary_weeks": float(complementary),
        "total_weeks": float(total),
    }


def refresh_cti_duration(student):
    """Calcule et persiste la durée de mobilité dans MobilityDuration."""
    from app.cti.models import MobilityDuration

    data = compute_cti_duration(student)
    obj, _ = MobilityDuration.objects.update_or_create(student=student, defaults=data)
    return obj


def get_student_mobility_history(student) -> dict:
    """
    Retourne l'historique complet des mobilités d'un étudiant pour l'interface admin.

    Inclut : tous les échanges publiés, tous les stages (dont hors international),
    toutes les mobilités complémentaires quel que soit leur statut.
    Les totaux portent uniquement sur les mobilités comptabilisables (validées/internationales).
    """
    from app.complementary.models import ComplementaryMobility
    from app.internships.models import Internship
    from app.outgoing.models import AssignmentResult

    exchanges = []
    for r in (
        AssignmentResult.objects.filter(
            annual_enrollment__student=student,
            assignment__status="published",
            agreement_year__isnull=False,
        )
        .select_related(
            "agreement_year__academic_year",
            "agreement_year__agreement__partner_university__country",
        )
        .order_by("-agreement_year__academic_year__start_date")
    ):
        ay = r.agreement_year
        univ = ay.agreement.partner_university
        exchanges.append(
            {
                "academic_year": ay.academic_year.label,
                "institution_name": univ.name,
                "country_name": univ.country.name_fr,
                "duration_weeks": ay.duration_weeks,
            }
        )

    internships = []
    for i in (
        Internship.objects.filter(student=student)
        .select_related("country", "academic_year")
        .order_by("-start_date")
    ):
        internships.append(
            {
                "academic_year": i.academic_year.label if i.academic_year else None,
                "company_name": i.company_name,
                "country_name": i.country.name_fr if i.country else None,
                "start_date": i.start_date,
                "end_date": i.end_date,
                "weeks_in_company": i.weeks_in_company,
                "is_international": i.country is not None and i.country.iso2 != "FR",
            }
        )

    complementary = []
    for m in (
        ComplementaryMobility.objects.filter(student=student)
        .select_related("destination_country", "academic_year")
        .order_by("-start_date")
    ):
        duration = _weeks_from_dates(m.start_date, m.end_date).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        complementary.append(
            {
                "id": m.id,
                "academic_year": m.academic_year.label,
                "experience_type": m.experience_type,
                "destination_country": m.destination_country.name_fr,
                "destination_institution": m.destination_institution or None,
                "start_date": m.start_date,
                "end_date": m.end_date,
                "duration_weeks": float(duration),
                "status": m.status,
            }
        )

    totals = compute_cti_duration(student)

    return {
        "ine": student.ine,
        "totals": totals,
        "exchanges": exchanges,
        "internships": internships,
        "complementary_mobilities": complementary,
    }
