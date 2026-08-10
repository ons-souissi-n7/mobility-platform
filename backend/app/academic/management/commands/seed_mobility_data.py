"""
Seed données de mobilité complémentaires :
  - Étudiants entrants (IncomingStudent) — 6-8 par année
  - Stages internationaux (Internship) — 5-7 par année
  - Mobilités complémentaires (ComplementaryMobility) — 4-5 par année

Couvre les 4 années académiques (2022-2023, 2023-2024, 2024-2025, 2025-2026).
Idempotent : ne crée pas de doublons si relancé.
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

random.seed(99)

INCOMING_DATA = [
    # (civility, first, last, country_iso2, origin_university_name, dept_code, duration_weeks)
    ("M.", "Erik", "LINDQVIST", "SE", "KTH Stockholm", "SN", 20),
    ("Mme", "María", "RODRÍGUEZ", "ES", "Universidad Politécnica de Madrid", "3EA", 24),
    ("M.", "Marco", "FERRARI", "IT", "Politecnico di Milano", "MF2E", 20),
    ("Mme", "Anna", "MÜLLER", "DE", "TU Berlin", "SN", 18),
    ("M.", "Jan", "NOWAK", "PL", "Warsaw University of Technology", "3EA", 20),
    ("Mme", "Sofia", "JOHANSSON", "SE", "Lund University", "MF2E", 20),
    ("M.", "Pedro", "ALVES", "PT", "Instituto Superior Técnico", "SN", 24),
    ("Mme", "Ingrid", "HANSEN", "NO", "NTNU Trondheim", "3EA", 20),
    ("M.", "Lukas", "BAUER", "DE", "ETH Zurich", "MF2E", 20),
    ("Mme", "Chiara", "RICCI", "IT", "Politecnico di Torino", "SN", 18),
    ("M.", "Carlos", "JIMÉNEZ", "ES", "Universidad de Sevilla", "3EA", 20),
    ("Mme", "Emma", "SVENSSON", "SE", "Uppsala University", "MF2E", 24),
    ("M.", "Thomas", "SCHMIDT", "DE", "RWTH Aachen", "SN", 20),
    ("Mme", "Laura", "COSTA", "PT", "Universidade do Porto", "3EA", 20),
    ("M.", "Filip", "KOWALSKI", "PL", "AGH University", "MF2E", 20),
    ("Mme", "Giulia", "MARINO", "IT", "University of Bologna", "SN", 18),
    ("M.", "Anders", "ERIKSSON", "SE", "Chalmers University", "3EA", 20),
    ("Mme", "Beatriz", "SANTOS", "PT", "Universidade de Coimbra", "MF2E", 20),
    ("M.", "Hans", "FISCHER", "DE", "TU Munich", "SN", 24),
    ("Mme", "Lena", "BERG", "NO", "University of Oslo", "3EA", 20),
    ("M.", "Rafael", "MORENO", "ES", "Universidad Complutense", "MF2E", 20),
    ("Mme", "Marta", "WIŚNIEWSKA", "PL", "Wrocław UT", "SN", 20),
    ("M.", "Lorenzo", "ESPOSITO", "IT", "La Sapienza", "3EA", 18),
    ("Mme", "Astrid", "LARSSON", "SE", "Linköping University", "MF2E", 20),
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

COMPLEMENTARY_DATA = [
    # (experience_type, country_iso2, institution, start_month, duration_days)
    ("Summer school", "GB", "Imperial College London", 7, 21),
    ("Summer school", "DE", "TU Munich", 7, 28),
    ("Summer school", "SE", "KTH Stockholm", 7, 21),
    ("Programme d'échange court", "ES", "Universidad Complutense", 2, 90),
    ("Programme d'échange court", "IT", "Politecnico di Milano", 9, 90),
    ("Programme d'échange court", "PT", "Instituto Superior Técnico", 2, 90),
    ("Projet de recherche", "CH", "EPFL", 6, 60),
    ("Projet de recherche", "DE", "RWTH Aachen", 5, 60),
    ("Projet de recherche", "NL", "TU Delft", 6, 45),
    ("Volunteering international", "MA", "ONEE", 6, 30),
    ("Volunteering international", "SN", "Institut Polytechnique de Thiès", 6, 30),
    ("Programme humanitaire", "MA", "Université Cadi Ayyad", 7, 30),
    ("Conférence internationale", "US", "MIT", 6, 7),
    ("Conférence internationale", "JP", "Université de Tokyo", 9, 10),
    ("Stage à l'étranger", "CA", "McGill University", 6, 90),
    ("Stage à l'étranger", "JP", "Université d'Osaka", 1, 60),
    ("Stage à l'étranger", "AU", "Université de Melbourne", 6, 90),
]

COUNTRY_CACHE: dict = {}
UNIVERSITY_CACHE: dict = {}


class Command(BaseCommand):
    help = "Seed étudiants entrants, stages et mobilités complémentaires sur 4 années"

    def handle(self, *args, **options):
        from app.academic.models import AcademicYear

        years = list(
            AcademicYear.objects.filter(
                label__in=["2022-2023", "2023-2024", "2024-2025", "2025-2026"]
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

    def _get_dept(self, code: str):
        from app.reference.models import Department

        return Department.objects.filter(code=code).first()

    def _get_university(self, name: str, country_iso2: str):
        from app.institutions.models import PartnerUniversity

        if name not in UNIVERSITY_CACHE:
            country = self._get_country(country_iso2)
            univ, _ = PartnerUniversity.objects.get_or_create(
                name=name,
                defaults={"country": country, "short_name": name[:50]},
            )
            UNIVERSITY_CACHE[name] = univ
        return UNIVERSITY_CACHE[name]

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

        per_year = [6, 7, 7, 8]
        cat = self._get_mobility_category()
        pool = INCOMING_DATA[:]
        random.shuffle(pool)
        pool = pool * 4  # enough for all years
        idx = 0

        total = 0
        for year, count in zip(years, per_year, strict=False):
            created = 0
            for _ in range(count):
                entry = pool[idx % len(INCOMING_DATA)]
                idx += 1
                civ, first, last, iso2, univ_name, dept_code, weeks = entry

                country = self._get_country(iso2)
                dept = self._get_dept(dept_code)
                univ = self._get_university(univ_name, iso2)

                if IncomingStudent.objects.filter(
                    academic_year=year,
                    last_name=last,
                    first_name=first,
                ).exists():
                    continue

                IncomingStudent.objects.create(
                    academic_year=year,
                    civility=civ,
                    first_name=first,
                    last_name=last,
                    country=country,
                    origin_university=univ,
                    origin_university_name=univ_name,
                    department=dept,
                    mobility_category=cat,
                    duration=weeks,
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

        per_year = [5, 6, 7, 6]
        pool = INTERNSHIP_DATA[:]
        random.shuffle(pool)
        pool = pool * 4
        idx = 0

        total = 0
        for year, count in zip(years, per_year, strict=False):
            start_yr = year.start_date.year
            created = 0
            for _ in range(count):
                entry = pool[idx % len(INTERNSHIP_DATA)]
                idx += 1
                company, city, iso2, title, itype, weeks = entry

                student = self._get_student_for_year(year)
                if not student:
                    continue

                start = date(start_yr + 1, 3, 1) + timedelta(days=random.randint(0, 30))
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

        per_year = [4, 4, 5, 4]
        pool = COMPLEMENTARY_DATA[:]
        random.shuffle(pool)
        pool = pool * 4
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

                # Valider les années passées, laisser "pending" 2025-2026
                if year.label != "2025-2026":
                    ComplementaryMobility.objects.filter(pk=mob.pk).update(
                        status="validated"
                    )

                created += 1

            total += created
            self.stdout.write(f"  Complémentaires {year.label} : {created} créées")

        self.stdout.write(f"  Total complémentaires : {total}")
