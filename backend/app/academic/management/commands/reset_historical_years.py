"""
Réinitialise les données rattachées à une année universitaire (années, accords-année,
vœux, étudiants, affectations, stages) et reconstruit un historique de campagnes
clôturées à partir des données de référence existantes.

Ne touche pas aux données de référence : pays, départements, niveaux, parcours,
universités partenaires, cadres de mobilité (MobilityCategory), accords (Agreement).

Chaque année historique est menée jusqu'à publication puis clôture en passant par
les vraies transitions FSM (AcademicYear + Assignment) et le vrai algorithme
Gale-Shapley, pour obtenir un historique cohérent avec le fonctionnement réel de
l'application.

L'année « courante » n'est volontairement pas créée : c'est à l'utilisateur de la
créer depuis l'interface une fois l'historique en place.

`random` sert uniquement à générer des étudiants/vœux de démonstration
plausibles (jamais un token, un mot de passe ou une décision de sécurité) —
la graine (`--seed`) est même paramétrable pour reproduire un jeu de données.
Sans objet pour les hotspots Sonar "pseudorandom number generator" (S2245).
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

FIRST_NAMES_F = [
    "Léa",
    "Camille",
    "Sophie",
    "Lucie",
    "Clara",
    "Marie",
    "Claire",
    "Elisa",
    "Emma",
    "Anaïs",
    "Chloé",
    "Pauline",
    "Manon",
    "Julie",
    "Aurélie",
    "Océane",
    "Nadia",
    "Amina",
    "Ana",
    "Yuki",
    "Elena",
    "Astrid",
    "Ingrid",
    "Fatima",
]
FIRST_NAMES_M = [
    "Alexandre",
    "Nicolas",
    "Julien",
    "Maxime",
    "Lucas",
    "Thomas",
    "Antoine",
    "Romain",
    "Baptiste",
    "Valentin",
    "Thibault",
    "Théo",
    "Alexis",
    "Quentin",
    "Sébastien",
    "Mathieu",
    "Carlos",
    "Mehdi",
    "Jan",
    "Omar",
    "Marco",
    "Pietro",
    "Tomás",
    "David",
    "Lars",
    "Ricardo",
]
LAST_NAMES = [
    "MARTIN",
    "DUPONT",
    "BERNARD",
    "PETIT",
    "MOREAU",
    "LAURENT",
    "SIMON",
    "MICHEL",
    "GARCIA",
    "ARNAUD",
    "LEROY",
    "DUBOIS",
    "GAUTHIER",
    "ROUSSEAU",
    "FONTAINE",
    "VINCENT",
    "MERCIER",
    "PICARD",
    "KOWALSKI",
    "MULLER",
    "BENNANI",
    "POPESCU",
    "BONNET",
    "LEBRUN",
    "MASSON",
    "CARON",
    "RENARD",
    "GIRARD",
    "BIANCHI",
    "HANSEN",
    "GOMES",
    "TANAKA",
    "SILVA",
    "CHEN",
    "LARSEN",
]
NATIONALITY_POOL = [
    "FR",
    "FR",
    "FR",
    "FR",
    "FR",
    "ES",
    "DE",
    "IT",
    "PT",
    "PL",
    "SE",
    "DK",
    "NO",
    "CA",
    "MA",
    "JP",
    "CH",
    "GB",
]
# Codes réels du référentiel niveaux (app/reference/fixtures/levels.json) :
# 1ING/2ING/3ING, 1M/2M, 1DOC/2DOC/3DOC — "ING"/"M1"/"M2"/"L3" seuls n'existent
# pas, ce qui provoquait un level_id NULL (IntegrityError) à la création des
# inscriptions. Cursus ingénieur dominant (mobilité sortante concentrée en
# 2ING/3ING, cf. seed_dev_data), quelques Master pour la diversité.
LEVEL_WEIGHTS = [("2ING", 5), ("3ING", 3), ("1ING", 2), ("1M", 1), ("2M", 1)]

HISTORICAL_LABELS = ["2022-2023", "2023-2024", "2024-2025"]


class Command(BaseCommand):
    help = (
        "Vide les données liées aux années (années, accords-année, vœux, étudiants, "
        "affectations, stages) et régénère un historique de campagnes clôturées, sans "
        "toucher aux données de référence ni créer l'année courante."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--labels",
            nargs="+",
            default=None,
            help=f"Libellés des années historiques à générer (défaut : {', '.join(HISTORICAL_LABELS)})",
        )
        parser.add_argument(
            "--students-per-dept",
            type=int,
            default=10,
            help="Nombre d'étudiants créés par département et par année (défaut: 10)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Graine aléatoire pour la reproductibilité (défaut: 42)",
        )

    def handle(self, *args, **options):
        labels = options["labels"] or HISTORICAL_LABELS
        n_per_dept = options["students_per_dept"]
        random.seed(options["seed"])  # NOSONAR (S2245) — donnée de démo

        with transaction.atomic():
            self._wipe_year_scoped_data()
            depts, levels_by_code, parcours_by_dept, countries = (
                self._load_reference_data()
            )
            agreements, agreement_depts_by_agreement = self._load_agreements()

            if not agreements:
                self.stderr.write(
                    self.style.ERROR(
                        "Aucun accord (Agreement) en base — impossible de générer un "
                        "historique sans accords existants."
                    )
                )
                return

            for label in labels:
                self._build_year(
                    label,
                    n_per_dept,
                    depts,
                    levels_by_code,
                    parcours_by_dept,
                    countries,
                    agreements,
                    agreement_depts_by_agreement,
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Historique reconstruit : {', '.join(labels)}.")
        )
        self.stdout.write(
            "  → Les données de référence (pays, départements, niveaux, parcours, "
            "universités, cadres de mobilité, accords) n'ont pas été modifiées.\n"
            "  → Aucune année courante n'a été créée — crée-la depuis l'interface."
        )

    # ────────────────────────────────────────────────────────────────────────
    # Suppression des données liées à une année
    # ────────────────────────────────────────────────────────────────────────

    def _wipe_year_scoped_data(self):
        from app.internships.models import Internship
        from app.mobility.models import AgreementYear, AgreementYearDepartment
        from app.outgoing.models import Assignment, AssignmentResult
        from app.students.models import AnnualEnrollment, Student, StudentWish

        counts = []
        counts.append(("Stages", Internship.objects.all().delete()[0]))
        counts.append(
            ("Résultats d'affectation", AssignmentResult.objects.all().delete()[0])
        )
        counts.append(("Affectations", Assignment.objects.all().delete()[0]))
        counts.append(("Vœux", StudentWish.objects.all().delete()[0]))
        counts.append(
            ("Inscriptions annuelles", AnnualEnrollment.objects.all().delete()[0])
        )
        counts.append(("Étudiants", Student.objects.all().delete()[0]))
        counts.append(
            ("Quotas accord-année", AgreementYearDepartment.objects.all().delete()[0])
        )
        counts.append(("Accords-année", AgreementYear.objects.all().delete()[0]))

        from app.academic.models import AcademicYear

        counts.append(("Années universitaires", AcademicYear.objects.all().delete()[0]))

        for label, n in counts:
            self.stdout.write(f"  {label} supprimés : {n}")

    # ────────────────────────────────────────────────────────────────────────
    # Chargement des données de référence (non modifiées)
    # ────────────────────────────────────────────────────────────────────────

    def _load_reference_data(self):
        from app.reference.models import Country, Department, Level, Parcours

        depts = list(Department.objects.all())
        levels_by_code = {lv.code: lv for lv in Level.objects.all()}
        parcours_by_dept: dict[str, list] = {}
        for p in Parcours.objects.select_related("department").all():
            parcours_by_dept.setdefault(p.department.code, []).append(p)
        countries = {
            c.iso2: c for c in Country.objects.filter(iso2__in=set(NATIONALITY_POOL))
        }

        self.stdout.write("  Départements : " + ", ".join(d.code for d in depts))
        return depts, levels_by_code, parcours_by_dept, countries

    def _load_agreements(self):
        from app.mobility.models import Agreement, AgreementDepartment

        agreements = list(Agreement.objects.prefetch_related("levels").all())
        agreement_depts_by_agreement: dict[int, list] = {}
        for ad in AgreementDepartment.objects.select_related("department").all():
            agreement_depts_by_agreement.setdefault(ad.agreement_id, []).append(ad)

        self.stdout.write(f"  Accords existants réutilisés : {len(agreements)}")
        return agreements, agreement_depts_by_agreement

    # ────────────────────────────────────────────────────────────────────────
    # Construction d'une année historique complète
    # ────────────────────────────────────────────────────────────────────────

    def _build_year(
        self,
        label,
        n_per_dept,
        depts,
        levels_by_code,
        parcours_by_dept,
        countries,
        agreements,
        agreement_depts_by_agreement,
    ):
        from app.academic.models import AcademicYear
        from app.mobility.models import AgreementYear, AgreementYearDepartment

        start_year = int(label.split("-")[0])
        start_date = date(start_year, 9, 1)
        end_date = date(start_year + 1, 8, 31)

        year = AcademicYear.objects.create(
            label=label,
            start_date=start_date,
            end_date=end_date,
            wishes_open_date=date(start_year, 10, 1),
            wishes_close_date=date(start_year, 11, 30),
        )
        self.stdout.write(self.style.SUCCESS(f"\n── Année {label} (pk={year.pk}) ──"))

        # ── Accords-année + quotas ────────────────────────────────────────
        ay_by_agreement_id: dict[int, AgreementYear] = {}
        for agreement in agreements:
            n7_places = max(agreement.inp_total_places, 2)
            ay = AgreementYear.objects.create(
                agreement=agreement,
                academic_year=year,
                is_active=True,
                n7_places=n7_places,
                inp_total_places=n7_places,
            )
            ay_by_agreement_id[agreement.id] = ay

            linked = agreement_depts_by_agreement.get(agreement.id, [])
            if linked:
                share = max(n7_places // len(linked), 1)
                for ad in linked:
                    AgreementYearDepartment.objects.create(
                        agreement_year=ay,
                        agreement_department=ad,
                        estimated_places=share,
                    )

        AgreementYear.objects.filter(academic_year=year).update(
            is_validated=True,
            validated_by="reset_historical_years",
            validated_at=timezone.now(),
        )
        self.stdout.write(f"  Accords-année créés : {len(ay_by_agreement_id)}")

        # Index dept_code -> [(AgreementYear, allowed_level_ids)]
        dept_to_ays: dict[str, list[tuple]] = {}
        for agreement in agreements:
            ay = ay_by_agreement_id[agreement.id]
            allowed_level_ids = {lv.id for lv in agreement.levels.all()}
            for ad in agreement_depts_by_agreement.get(agreement.id, []):
                dept_to_ays.setdefault(ad.department.code, []).append(
                    (ay, allowed_level_ids)
                )

        # ── Étudiants + inscriptions ───────────────────────────────────────
        enrollments = self._create_students(
            year,
            start_year,
            n_per_dept,
            depts,
            levels_by_code,
            parcours_by_dept,
            countries,
        )

        # ── Vœux ────────────────────────────────────────────────────────────
        n_wishes = self._create_wishes(enrollments, dept_to_ays)
        self.stdout.write(
            f"  Étudiants créés : {len(enrollments)} — Vœux créés : {n_wishes}"
        )

        # ── FSM : mener la campagne jusqu'à publication puis clôture ────────
        self._run_campaign(year, end_date)

    def _create_students(
        self,
        year,
        start_year,
        n_per_dept,
        depts,
        levels_by_code,
        parcours_by_dept,
        countries,
    ):
        from app.students.models import AnnualEnrollment, GenderChoice, Student

        enrollments = []
        for dept in depts:
            parcours_list = parcours_by_dept.get(dept.code, [])
            for i in range(1, n_per_dept + 1):
                is_female = random.random() < 0.45  # NOSONAR (S2245) — donnée de démo
                first = random.choice(  # NOSONAR (S2245) — donnée de démo
                    FIRST_NAMES_F if is_female else FIRST_NAMES_M
                )
                last = random.choice(LAST_NAMES)  # NOSONAR (S2245) — donnée de démo
                ine = f"{start_year}{dept.code}{i:03d}"
                iso2 = random.choice(  # NOSONAR (S2245) — donnée de démo
                    NATIONALITY_POOL
                )
                level_code = random.choices(  # NOSONAR (S2245) — donnée de démo
                    [c for c, _ in LEVEL_WEIGHTS], weights=[w for _, w in LEVEL_WEIGHTS]
                )[0]
                level = levels_by_code.get(level_code)

                student = Student.objects.create(
                    ine=ine,
                    first_name=first,
                    last_name=last,
                    email=f"{first.lower()}.{last.lower()}.{ine}@etu.inp-toulouse.fr",
                    gender=GenderChoice.FEMALE if is_female else GenderChoice.MALE,
                    nationality=countries.get(iso2),
                )
                parcours_choice = (
                    random.choice(parcours_list)  # NOSONAR (S2245) — donnée de démo
                    if parcours_list
                    else None
                )
                gpa_value = round(
                    random.uniform(2.4, 3.95),
                    2,  # NOSONAR (S2245) — donnée de démo
                )
                is_alternant_value = (
                    random.random() < 0.25  # NOSONAR (S2245) — donnée de démo
                )
                is_scholarship_value = (
                    random.random() < 0.2  # NOSONAR (S2245) — donnée de démo
                )
                enrollment = AnnualEnrollment.objects.create(
                    student=student,
                    academic_year=year,
                    department=dept,
                    level=level,
                    parcours=parcours_choice,
                    gpa=gpa_value,
                    is_alternant=is_alternant_value,
                    is_scholarship=is_scholarship_value,
                )
                enrollments.append(enrollment)
        return enrollments

    def _create_wishes(self, enrollments, dept_to_ays):
        from app.students.models import StudentWish

        created = 0
        for enrollment in enrollments:
            eligible = [
                ay
                for ay, allowed_level_ids in dept_to_ays.get(
                    enrollment.department.code, []
                )
                if not allowed_level_ids or enrollment.level_id in allowed_level_ids
            ]
            if not eligible:
                continue
            n = min(
                len(eligible),
                random.randint(1, 3),  # NOSONAR (S2245) — donnée de démo
            )
            chosen = random.sample(eligible, n)  # NOSONAR (S2245) — donnée de démo
            for rank, ay in enumerate(chosen, start=1):
                StudentWish.objects.create(
                    annual_enrollment=enrollment, agreement_year=ay, rank=rank
                )
                created += 1
        return created

    def _run_campaign(self, year, end_date):
        from app.academic.models import AcademicYear
        from app.outgoing.models import Assignment, AssignmentStatus
        from app.outgoing.services.task_runners import run_gale_shapley

        year.open_recommendation()
        year.save(update_fields=["status", "updated_at"])
        year.start_candidature()
        year.save(update_fields=["status", "updated_at"])
        year.close_wishes()
        year.save(update_fields=["status", "updated_at"])
        year.launch_assignment()
        year.save(update_fields=["status", "updated_at"])

        run_gale_shapley(year.id, triggered_by="reset_historical_years")

        # FSMField(protected=True) est incompatible avec refresh_from_db() — refetch propre
        year = AcademicYear.objects.get(pk=year.id)
        year.publish_results()
        year.save(update_fields=["status", "updated_at"])

        assignment = (
            Assignment.objects.filter(academic_year=year)
            .order_by("-created_at")
            .first()
        )
        if assignment and assignment.status == AssignmentStatus.PROPOSED:
            assignment.validate()
            assignment.save(update_fields=["status", "updated_at"])
        if assignment and assignment.status == AssignmentStatus.VALIDATED:
            assignment.publish()
            assignment.save(update_fields=["status", "updated_at"])

        # close() exige source=FINALIZATION — finalize_cti() est l'étape
        # intermédiaire obligatoire entre PUBLISHED et CLOSED (cf. FSM
        # academic.models.AcademicYear), sans quoi TransitionNotAllowed.
        year.finalize_cti()
        year.save(update_fields=["status", "updated_at"])

        year.close()
        year.closed_at = timezone.make_aware(
            timezone.datetime.combine(
                end_date + timedelta(days=30), timezone.datetime.min.time()
            )
        )
        year.save(update_fields=["status", "closed_at", "updated_at"])

        rate = (
            round(assignment.assigned_count / assignment.total_students * 100, 1)
            if assignment and assignment.total_students
            else 0
        )
        self.stdout.write(
            f"  Campagne clôturée — {assignment.assigned_count if assignment else 0}/"
            f"{assignment.total_students if assignment else 0} affectés ({rate}%)"
        )
