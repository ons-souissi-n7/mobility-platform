"""
Génère les vœux (StudentWish) de tous les étudiants inscrits sur une année
comme étant leur top-3 de recommandations du moteur ML
(app.recommendation.services.model) — même logique que l'endpoint
GET /students/{ine}/recommendations/, mais appliquée en masse et persistée,
pour pouvoir ensuite comparer l'affectation réelle (Gale-Shapley) aux
recommandations et juger la pertinence du modèle.

Écrase les vœux existants de chaque étudiant traité.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from app.academic.models import AcademicYear
from app.recommendation.services.historical_rate import compute_historical_rates
from app.recommendation.services.model import score_destinations, train_model
from app.students.models import AnnualEnrollment, StudentWish
from app.students.services.agreement_eligibility import eligible_agreement_years

TOP_N = 3


class Command(BaseCommand):
    help = (
        "Génère les vœux de tous les étudiants inscrits sur une année comme "
        "leur top-3 de recommandations du modèle ML. Écrase les vœux existants."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--year", required=True, help="Libellé de l'année académique, ex: 2026-2027"
        )

    @transaction.atomic
    def handle(self, *_args, **options):
        label = options["year"]
        try:
            year = AcademicYear.objects.get(label=label)
        except AcademicYear.DoesNotExist as exc:
            raise CommandError(f"Année '{label}' introuvable.") from exc

        enrollments = list(
            AnnualEnrollment.objects.filter(
                academic_year=year, deleted_at__isnull=True
            ).select_related("department", "level", "student__nationality")
        )
        if not enrollments:
            raise CommandError(f"Aucune inscription active pour l'année '{label}'.")

        # Calculés une seule fois pour toute l'année plutôt qu'à chaque
        # étudiant : compute_historical_rates()/train_model() sont coûteux
        # (agrégation + validation croisée) et ne dépendent pas de l'étudiant.
        rates = compute_historical_rates()
        pipeline = train_model(rates=rates)
        model_based = pipeline is not None
        self.stdout.write(
            "Modèle "
            + (
                "entraîné (AUC suffisant)."
                if model_based
                else "non disponible — repli sur le taux historique / GPA."
            )
        )

        generated = 0
        skipped_no_eligible = 0
        for enrollment in enrollments:
            eligible = eligible_agreement_years(enrollment, year.id)
            if not eligible:
                skipped_no_eligible += 1
                continue

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
            ranked = sorted(
                zip(eligible, scores, strict=True),
                key=lambda pair: (
                    pair[1]
                    if pair[1] is not None
                    else rates.get(pair[0].agreement_id, 0.0)
                ),
                reverse=True,
            )

            StudentWish.objects.filter(annual_enrollment=enrollment).delete()
            for rank, (ay, _score) in enumerate(ranked[:TOP_N], start=1):
                StudentWish.objects.create(
                    annual_enrollment=enrollment, agreement_year=ay, rank=rank
                )
            generated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{generated} étudiant(s) traité(s) : vœux remplacés par leur top-{TOP_N} "
                f"recommandé ({skipped_no_eligible} sans destination éligible, ignoré(s))."
            )
        )
