"""
Seed données de mobilité complémentaires :
  - Étudiants entrants (IncomingStudent) — 60 à 130 par année, université
    d'origine tirée parmi les PartnerUniversity du référentiel (nationalité
    et pays qui en découlent, donc diversifiés sur les ~35 pays couverts)
  - Stages internationaux (Internship) — 40 à 50 par année, types PFA/Stage
    3A/PFE en rotation
  - Mobilités complémentaires (ComplementaryMobility) — ~10 par année,
    états pending/validated/rejected répartis via les vraies transitions FSM

Couvre les 6 années académiques (2020-2021 à 2025-2026).
Idempotent : ne crée pas de doublons si relancé.

`random` est utilisé uniquement pour mélanger/piocher des données de démo
(jamais pour un token, un mot de passe ou une décision de sécurité) — la
graine fixe (99) est même volontaire pour que le jeu de données généré soit
reproductible d'un lancement à l'autre. Sans objet pour les hotspots Sonar
"pseudorandom number generator" (S2245) ci-dessous.
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

random.seed(99)  # NOSONAR (S2245) — génération de données de démo, pas de sécurité

# Étudiants entrants : noms/prénoms génériques piochés au hasard, l'université
# d'origine (et donc la nationalité et le pays) étant tirée parmi les 35
# PartnerUniversity existantes (cf. generate_fixtures.py) pour rester cohérent
# avec le référentiel réel plutôt que de créer des universités ad hoc.
INCOMING_FIRST_NAMES_F = [
    "Maria",
    "Anna",
    "Sofia",
    "Laura",
    "Elena",
    "Chiara",
    "Ingrid",
    "Astrid",
    "Emma",
    "Marta",
    "Beatriz",
    "Giulia",
    "Lena",
    "Ana",
    "Yuki",
    "Mei",
    "Priya",
    "Fatima",
    "Aisha",
    "Hana",
    "Charlotte",
    "Freya",
    "Noor",
    "Sakura",
]
INCOMING_FIRST_NAMES_M = [
    "Erik",
    "Marco",
    "Jan",
    "Pedro",
    "Lukas",
    "Carlos",
    "Thomas",
    "Filip",
    "Anders",
    "Hans",
    "Rafael",
    "Lorenzo",
    "David",
    "Wei",
    "Hiroshi",
    "Arjun",
    "Mohammed",
    "Omar",
    "Liam",
    "James",
    "Diego",
    "Matteo",
    "Sven",
    "Kenji",
]
INCOMING_LAST_NAMES = [
    "MÜLLER",
    "GARCÍA",
    "ROSSI",
    "SILVA",
    "KOWALSKI",
    "JOHANSSON",
    "HANSEN",
    "FERRARI",
    "SANTOS",
    "NOWAK",
    "SCHMIDT",
    "COSTA",
    "ESPOSITO",
    "LARSSON",
    "TANAKA",
    "CHEN",
    "PATEL",
    "KIM",
    "AL-RASHID",
    "AVRAMOV",
    "MACDONALD",
    "MARTINS",
    "PEREIRA",
    "DUBOIS",
    "JIMÉNEZ",
    "WIŚNIEWSKA",
    "RICCI",
    "BERG",
]

INTERNSHIP_DATA = [
    # (company, city, country_iso2, title, type, weeks)
    (
        "Airbus",
        "Toulouse",
        "FR",
        "Stage ingénieur systèmes embarqués",
        "stage_fin_etudes",
        24,
    ),
    (
        "Thales",
        "Paris",
        "FR",
        "Stage développement logiciel temps réel",
        "stage_fin_etudes",
        24,
    ),
    (
        "Siemens",
        "Munich",
        "DE",
        "Internship — Power Electronics",
        "stage_fin_etudes",
        24,
    ),
    (
        "Bosch",
        "Stuttgart",
        "DE",
        "Internship — Embedded Systems",
        "stage_fin_etudes",
        20,
    ),
    ("ABB", "Zurich", "CH", "Stage ingénieur automatisation", "stage_fin_etudes", 24),
    (
        "Rolls-Royce",
        "Derby",
        "GB",
        "Internship — Aerospace Engineering",
        "stage_fin_etudes",
        24,
    ),
    (
        "Ericsson",
        "Stockholm",
        "SE",
        "Internship — Telecom Software",
        "stage_fin_etudes",
        20,
    ),
    (
        "Alstom",
        "Saint-Ouen",
        "FR",
        "Stage ferroviaire — systèmes traction",
        "stage_fin_etudes",
        24,
    ),
    (
        "Michelin",
        "Clermont",
        "FR",
        "Stage conception mécanique",
        "stage_fin_etudes",
        20,
    ),
    (
        "STMicroelectronics",
        "Crolles",
        "FR",
        "Stage microélectronique",
        "stage_fin_etudes",
        24,
    ),
    ("Nokia", "Espoo", "FI", "Internship — 5G Systems", "stage_fin_etudes", 20),
    (
        "Schneider Electric",
        "Grenoble",
        "FR",
        "Stage énergie renouvelable",
        "stage_fin_etudes",
        24,
    ),
    (
        "Continental",
        "Hanovre",
        "DE",
        "Internship — Automotive Safety",
        "stage_fin_etudes",
        20,
    ),
    (
        "Safran",
        "Paris",
        "FR",
        "Stage aéronautique — propulsion",
        "stage_fin_etudes",
        24,
    ),
    (
        "GE Vernova",
        "Baden",
        "CH",
        "Internship — Grid Technology",
        "stage_fin_etudes",
        20,
    ),
    (
        "TotalEnergies",
        "Paris",
        "FR",
        "Stage transition énergétique",
        "stage_fin_etudes",
        24,
    ),
    (
        "Capgemini",
        "Madrid",
        "ES",
        "Internship — Data Engineering",
        "stage_fin_etudes",
        20,
    ),
    (
        "CERN",
        "Genève",
        "CH",
        "Stage physique des accélérateurs",
        "stage_fin_etudes",
        24,
    ),
    ("Renault", "Paris", "FR", "Stage véhicule électrique", "stage_fin_etudes", 20),
    (
        "Dassault Aviation",
        "Saint-Cloud",
        "FR",
        "Stage simulation aérodynamique",
        "stage_fin_etudes",
        24,
    ),
    (
        "Philips",
        "Amsterdam",
        "NL",
        "Internship — Medical Devices",
        "stage_fin_etudes",
        20,
    ),
    ("EDF", "Lyon", "FR", "Stage nucléaire — sûreté", "stage_fin_etudes", 24),
    ("BMW", "Munich", "DE", "Internship — EV Battery Systems", "stage_fin_etudes", 20),
    (
        "Valeo",
        "Paris",
        "FR",
        "Stage ADAS — vision par ordinateur",
        "stage_fin_etudes",
        24,
    ),
    ("L'Oréal", "Paris", "FR", "Stage formulation cosmétique", "stage_fin_etudes", 20),
    ("SNCF", "Paris", "FR", "Stage infrastructure ferroviaire", "stage_fin_etudes", 24),
    ("Engie", "Paris", "FR", "Stage hydrogène vert", "stage_fin_etudes", 20),
]

# Types d'expérience répétés dans COMPLEMENTARY_DATA ci-dessous.
EXPERIENCE_SUMMER_SCHOOL = "Summer school"
EXPERIENCE_SHORT_EXCHANGE = "Programme d'échange court"
EXPERIENCE_RESEARCH_PROJECT = "Projet de recherche"
EXPERIENCE_INTERNSHIP_ABROAD = "Stage à l'étranger"

COMPLEMENTARY_DATA = [
    # (experience_type, country_iso2, institution, start_month, duration_days)
    (EXPERIENCE_SUMMER_SCHOOL, "GB", "Imperial College London", 7, 21),
    (EXPERIENCE_SUMMER_SCHOOL, "DE", "TU Munich", 7, 28),
    (EXPERIENCE_SUMMER_SCHOOL, "SE", "KTH Stockholm", 7, 21),
    (EXPERIENCE_SHORT_EXCHANGE, "ES", "Universidad Complutense", 2, 90),
    (EXPERIENCE_SHORT_EXCHANGE, "IT", "Politecnico di Milano", 9, 90),
    (EXPERIENCE_SHORT_EXCHANGE, "PT", "Instituto Superior Técnico", 2, 90),
    (EXPERIENCE_RESEARCH_PROJECT, "CH", "EPFL", 6, 60),
    (EXPERIENCE_RESEARCH_PROJECT, "DE", "RWTH Aachen", 5, 60),
    (EXPERIENCE_RESEARCH_PROJECT, "NL", "TU Delft", 6, 45),
    ("Volunteering international", "MA", "ONEE", 6, 30),
    ("Volunteering international", "SN", "Institut Polytechnique de Thiès", 6, 30),
    ("Programme humanitaire", "MA", "Université Cadi Ayyad", 7, 30),
    ("Conférence internationale", "US", "MIT", 6, 7),
    ("Conférence internationale", "JP", "Université de Tokyo", 9, 10),
    (EXPERIENCE_INTERNSHIP_ABROAD, "CA", "McGill University", 6, 90),
    (EXPERIENCE_INTERNSHIP_ABROAD, "JP", "Université d'Osaka", 1, 60),
    (EXPERIENCE_INTERNSHIP_ABROAD, "AU", "Université de Melbourne", 6, 90),
    (EXPERIENCE_SUMMER_SCHOOL, "CH", "EPFL", 7, 21),
    (EXPERIENCE_SHORT_EXCHANGE, "NL", "TU Delft", 2, 90),
    (EXPERIENCE_RESEARCH_PROJECT, "SE", "KTH Stockholm", 5, 60),
    (EXPERIENCE_RESEARCH_PROJECT, "GB", "Imperial College London", 6, 45),
    ("Conférence internationale", "DE", "TU Munich", 10, 5),
    (EXPERIENCE_INTERNSHIP_ABROAD, "SG", "National University of Singapore", 1, 90),
    (EXPERIENCE_INTERNSHIP_ABROAD, "KR", "KAIST", 6, 90),
    (EXPERIENCE_SHORT_EXCHANGE, "IE", "Trinity College Dublin", 2, 90),
]

# Motifs de rejet plausibles pour diversifier les états de ComplementaryMobility
# (FSM pending/validated/rejected — cf. app.complementary.models).
REJECTION_REASONS = [
    "Justificatif manquant ou illisible",
    "Durée insuffisante pour être éligible",
    "Expérience hors du périmètre couvert (activité non académique)",
    "Dossier déposé hors délai",
]

COUNTRY_CACHE: dict = {}


class Command(BaseCommand):
    help = "Seed étudiants entrants, stages et mobilités complémentaires sur 6 années"

    def handle(self, *args, **options):
        from app.academic.models import AcademicYear

        years = list(
            AcademicYear.objects.filter(
                label__in=[
                    "2020-2021",
                    "2021-2022",
                    "2022-2023",
                    "2023-2024",
                    "2024-2025",
                    "2025-2026",
                ]
            ).order_by("start_date")
        )
        if not years:
            self.stderr.write(self.style.ERROR("Aucune année académique trouvée."))
            return

        self.stdout.write(f"Années trouvées : {[y.label for y in years]}")

        with transaction.atomic():
            self._seed_incoming(years)
            self._seed_internships(years)
            self._seed_complementary(years)

        self.stdout.write(self.style.SUCCESS("\n✓ Seed mobilités terminé."))

    # ────────────────────────────────────────────────────────────────────────
    # Helpers
    # ────────────────────────────────────────────────────────────────────────

    def _get_country(self, iso2: str):
        from app.reference.models import Country

        if iso2 not in COUNTRY_CACHE:
            COUNTRY_CACHE[iso2] = Country.objects.filter(iso2=iso2).first()
        return COUNTRY_CACHE[iso2]

    def _get_student_for_year(self, year):
        """Retourne un étudiant inscrit cette année-là (pour stages / complémentaires)."""
        from app.students.models import AnnualEnrollment

        enrollment = (
            AnnualEnrollment.objects.filter(academic_year=year)
            .select_related("student")
            .order_by("?")
            .first()
        )
        return enrollment.student if enrollment else None

    def _get_mobility_category(self):
        from app.mobility.models import MobilityCategory

        cat, _ = MobilityCategory.objects.get_or_create(
            name="Erasmus", defaults={"name": "Erasmus"}
        )
        return cat

    # ────────────────────────────────────────────────────────────────────────
    # Étudiants entrants
    # ────────────────────────────────────────────────────────────────────────

    def _seed_incoming(self, years):
        from app.incoming.models import IncomingStudent
        from app.institutions.models import PartnerUniversity
        from app.reference.models import Department

        cat = self._get_mobility_category()
        depts = list(Department.objects.all())
        universities = list(PartnerUniversity.objects.select_related("country").all())
        if not depts or not universities:
            self.stderr.write(
                self.style.WARNING(
                    "Départements ou universités partenaires absents — entrants "
                    "ignorés (charge d'abord les fixtures de référence)."
                )
            )
            return

        # Montée en charge sur 6 ans, de l'ordre de la centaine par an à partir
        # de 2022-2023 (diversité de nationalités/universités portée par le
        # tirage sur les 35 PartnerUniversity du référentiel).
        per_year = [60, 80, 100, 110, 120, 130]
        duration_weeks_choices = [16, 20, 24, 32]

        total = 0
        for year, count in zip(years, per_year, strict=False):
            created = 0
            for _ in range(count):
                is_female = random.random() < 0.48  # NOSONAR (S2245) — donnée de démo
                first = random.choice(  # NOSONAR (S2245) — donnée de démo
                    INCOMING_FIRST_NAMES_F if is_female else INCOMING_FIRST_NAMES_M
                )
                last = random.choice(INCOMING_LAST_NAMES)  # NOSONAR (S2245)
                univ = random.choice(universities)  # NOSONAR (S2245) — donnée de démo
                country = univ.country
                dept = random.choice(depts)  # NOSONAR (S2245) — donnée de démo
                weeks = random.choice(  # NOSONAR (S2245) — donnée de démo
                    duration_weeks_choices
                )
                birth_year = year.start_date.year - random.randint(  # NOSONAR (S2245)
                    20, 24
                )
                birth_date = date(
                    birth_year,
                    random.randint(1, 12),  # NOSONAR (S2245) — donnée de démo
                    random.randint(1, 28),  # NOSONAR (S2245) — donnée de démo
                )

                if IncomingStudent.objects.filter(
                    academic_year=year,
                    last_name=last,
                    first_name=first,
                    birth_date=birth_date,
                ).exists():
                    continue

                IncomingStudent.objects.create(
                    academic_year=year,
                    civility="Mme" if is_female else "M.",
                    first_name=first,
                    last_name=last,
                    country=country,
                    origin_university=univ,
                    origin_university_name=univ.name,
                    department=dept,
                    mobility_category=cat,
                    duration=str(weeks),
                    birth_date=birth_date,
                )
                created += 1

            total += created
            self.stdout.write(f"  Entrants {year.label} : {created} créés")

        self.stdout.write(f"  Total entrants : {total}")

    # ────────────────────────────────────────────────────────────────────────
    # Stages
    # ────────────────────────────────────────────────────────────────────────

    def _seed_internships(self, years):
        from app.internships.models import Internship

        per_year = [40, 42, 44, 46, 48, 50]
        pool = INTERNSHIP_DATA[:]
        random.shuffle(pool)  # NOSONAR (S2245) — donnée de démo
        pool = pool * 6
        idx = 0

        # Type de stage suivant le niveau : PFA (1ING, stage ouvrier/technicien,
        # court), Stage 3A (2ING, stage assistant-ingénieur), PFE (3ING/Master,
        # stage de fin d'études, le plus long). Rotation pour diversifier les
        # types plutôt que de tout marquer "stage_fin_etudes".
        type_rotation = [("PFA", 8, 12), ("Stage 3A", 16, 20), ("PFE", 20, 24)]

        total = 0
        for year, count in zip(years, per_year, strict=False):
            start_yr = year.start_date.year
            created = 0
            for _ in range(count):
                entry = pool[idx % len(INTERNSHIP_DATA)]
                itype, week_min, week_max = type_rotation[idx % len(type_rotation)]
                idx += 1
                company, city, iso2, title, _default_type, _default_weeks = entry
                weeks = random.randint(week_min, week_max)  # NOSONAR (S2245)

                student = self._get_student_for_year(year)
                if not student:
                    continue

                start = date(start_yr + 1, 3, 1) + timedelta(
                    days=random.randint(0, 30)  # NOSONAR (S2245) — donnée de démo
                )
                end = start + timedelta(weeks=weeks)

                if Internship.objects.filter(
                    student=student, company_name=company, start_date=start
                ).exists():
                    continue

                country = self._get_country(iso2)
                Internship.objects.create(
                    student=student,
                    academic_year=year,
                    company_name=company,
                    city=city,
                    country=country,
                    title=title,
                    internship_type=itype,
                    # "9 Justificatif reçu" est le seul statut Eudonet que le pipeline
                    # de sync retient (cf. sync_eudonet.py) — les stages qui arrivent
                    # jusqu'en base sont donc toujours dans cet état côté réel.
                    status_code="9",
                    status_label="Justificatif reçu",
                    start_date=start,
                    end_date=end,
                    weeks_in_company=weeks,
                )
                created += 1

            total += created
            self.stdout.write(f"  Stages {year.label} : {created} créés")

        self.stdout.write(f"  Total stages : {total}")

    # ────────────────────────────────────────────────────────────────────────
    # Mobilités complémentaires
    # ────────────────────────────────────────────────────────────────────────

    def _seed_complementary(self, years):
        from app.complementary.models import ComplementaryMobility

        per_year = [9, 10, 10, 11, 10, 10]
        pool = COMPLEMENTARY_DATA[:]
        random.shuffle(pool)  # NOSONAR (S2245) — donnée de démo
        pool = pool * 6
        idx = 0

        total = 0
        for year, count in zip(years, per_year, strict=False):
            start_yr = year.start_date.year
            created = 0
            for _ in range(count):
                entry = pool[idx % len(COMPLEMENTARY_DATA)]
                idx += 1
                exp_type, iso2, institution, start_month, duration_days = entry

                student = self._get_student_for_year(year)
                if not student:
                    continue

                country = self._get_country(iso2)
                if not country:
                    continue

                start = date(start_yr + (1 if start_month < 9 else 0), start_month, 1)
                end = start + timedelta(days=duration_days)

                mob, created_flag = ComplementaryMobility.objects.get_or_create(
                    student=student,
                    academic_year=year,
                    destination_institution=institution,
                    start_date=start,
                    defaults={
                        "experience_type": exp_type,
                        "destination_country": country,
                        "end_date": end,
                    },
                )

                if not created_flag:
                    continue

                # Diversité des états : la campagne en cours reste majoritairement
                # en attente ; les campagnes closes sont pour la plupart validées
                # mais gardent une part de rejets et de dossiers jamais traités,
                # comme dans un historique réel. Passe par les vraies transitions
                # FSM (validate/reject) plutôt qu'un update direct du statut.
                if year.label == "2025-2026":
                    outcome = random.choices(  # NOSONAR (S2245) — donnée de démo
                        ["pending", "validated", "rejected"], weights=[70, 20, 10]
                    )[0]
                else:
                    outcome = random.choices(  # NOSONAR (S2245) — donnée de démo
                        ["validated", "rejected", "pending"], weights=[75, 15, 10]
                    )[0]

                if outcome == "validated":
                    mob.validate()
                    mob.save(update_fields=["status", "updated_at"])
                elif outcome == "rejected":
                    reason = random.choice(REJECTION_REASONS)  # NOSONAR (S2245)
                    mob.reject(reason)
                    mob.save(update_fields=["status", "rejection_reason", "updated_at"])
                # sinon : reste "pending", état par défaut à la création

                created += 1

            total += created
            self.stdout.write(f"  Complémentaires {year.label} : {created} créées")

        self.stdout.write(f"  Total complémentaires : {total}")
