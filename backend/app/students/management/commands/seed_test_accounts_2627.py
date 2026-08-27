"""
Seed de 4 comptes étudiants de test pour la campagne 2026-2027.

Complète les comptes fake-cas existants (etudiant@etud.n7.fr / etudiant2@etud.n7.fr,
rattachés à 2025-2026 — cf. seed_dev_data) avec 4 nouveaux comptes couvrant les
combinaisons Boursier x FISE/FISA, utiles pour tester visuellement les colonnes
"Boursier" et "FISE/FISA" du tableau étudiants sur une année différente.

Deux profils sont représentés :
  - Anciens étudiants (Camille, Hugo) : une inscription 2025-2026 (historique)
    ET une nouvelle inscription 2026-2027 — cas d'un étudiant qui poursuit sa
    scolarité (Hugo passe FISE 2ING → FISA 3ING, cf. le commentaire
    is_alternant du modèle : "Les FISA choisissent leur mobilité en 3ème année").
  - Nouveaux étudiants (Léa, Nathan) : une seule inscription, 2026-2027 —
    aucun historique, première apparition dans le système.

Prérequis (fixtures déjà chargées) :
  - Départements SN, 3EA — loaddata departments
  - Niveaux 1ING, 2ING (FISE), 3ING (FISA) — loaddata levels
  - Pays France (FR) — loaddata countries
  - Année "2025-2026" — loaddata academic_years (nécessaire uniquement pour
    l'historique des anciens étudiants)

Crée aussi l'année "2026-2027" si absente.

Idempotent : peut être relancé plusieurs fois sans doublons.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from app.academic.models import AcademicYear
from app.reference.models import Country, Department, Level
from app.students.models import AnnualEnrollment, Student

PRIOR_YEAR_LABEL = "2025-2026"

# (first_name, last_name, ine, email, gender, dept_code,
#  prior_enrollment or None, current_enrollment)
# where each enrollment is (level_code, is_alternant, is_scholarship, gpa)
TEST_ACCOUNTS_2627 = [
    (
        "Camille",
        "ROUX",
        "20SN030FISE",
        "c.roux@etu.inp-toulouse.fr",
        "F",
        "SN",
        ("1ING", False, True, "13.20"),  # ancienne étudiante — 1ère année en 2025-2026
        ("2ING", False, True, "13.80"),
    ),
    (
        "Hugo",
        "MARTIN",
        "20SN031FISA",
        "h.martin@etu.inp-toulouse.fr",
        "M",
        "SN",
        ("2ING", False, True, "14.60"),  # ancien étudiant — FISE 2ING en 2025-2026
        ("3ING", True, True, "15.40"),  # bascule FISA en 3ème année
    ),
    (
        "Léa",
        "BERNARD",
        "203EA30FISE",
        "l.bernard@etu.inp-toulouse.fr",
        "F",
        "3EA",
        None,  # nouvelle étudiante — aucun historique
        ("2ING", False, False, "12.90"),
    ),
    (
        "Nathan",
        "PETIT",
        "203EA31FISA",
        "n.petit@etu.inp-toulouse.fr",
        "M",
        "3EA",
        None,  # nouvel étudiant — aucun historique
        ("3ING", True, False, "16.10"),
    ),
]


class Command(BaseCommand):
    help = "Seed 4 comptes étudiants de test (Boursier x FISE/FISA, anciens/nouveaux) pour 2026-2027."

    def _check_prerequisites(self, needs_prior_year: bool):
        for code in ("SN", "3EA"):
            if not Department.objects.filter(code=code).exists():
                raise CommandError(
                    f"Département '{code}' manquant. "
                    "Chargez d'abord : python manage.py loaddata departments"
                )
        for code in ("1ING", "2ING", "3ING"):
            if not Level.objects.filter(code=code).exists():
                raise CommandError(
                    f"Niveau '{code}' manquant. "
                    "Chargez d'abord : python manage.py loaddata levels"
                )
        if not Country.objects.filter(iso2="FR").exists():
            raise CommandError(
                "Pays France (FR) introuvable. "
                "Chargez d'abord : python manage.py loaddata countries"
            )
        if (
            needs_prior_year
            and not AcademicYear.objects.filter(label=PRIOR_YEAR_LABEL).exists()
        ):
            raise CommandError(
                f"Année '{PRIOR_YEAR_LABEL}' manquante (nécessaire pour l'historique des "
                "anciens étudiants). Chargez d'abord : python manage.py loaddata academic_years"
            )

    def _get_or_create_enrollment(self, student, year, dept, level_map, spec) -> bool:
        level_code, is_alternant, is_scholarship, gpa = spec
        _enrollment, created = AnnualEnrollment.objects.get_or_create(
            student=student,
            academic_year=year,
            defaults={
                "department": dept,
                "level": level_map[level_code],
                "gpa": gpa,
                "is_alternant": is_alternant,
                "is_scholarship": is_scholarship,
            },
        )
        return created

    @transaction.atomic
    def handle(self, *_args, **_options):
        needs_prior_year = any(row[6] is not None for row in TEST_ACCOUNTS_2627)
        self._check_prerequisites(needs_prior_year)

        year, year_created = AcademicYear.objects.get_or_create(
            label="2026-2027",
            defaults={
                "start_date": "2026-09-01",
                "end_date": "2027-08-31",
                "wishes_open_date": "2026-10-01",
                "wishes_close_date": "2026-11-30",
            },
        )
        self.stdout.write(
            f"Année 2026-2027 : {'créée' if year_created else 'déjà présente'} (id={year.id})"
        )
        prior_year = (
            AcademicYear.objects.get(label=PRIOR_YEAR_LABEL)
            if needs_prior_year
            else None
        )

        dept_map = {
            d.code: d for d in Department.objects.filter(code__in=["SN", "3EA"])
        }
        level_map = {
            level.code: level
            for level in Level.objects.filter(code__in=["1ING", "2ING", "3ING"])
        }
        france = Country.objects.get(iso2="FR")

        created_count = 0
        for (
            first,
            last,
            ine,
            email,
            gender,
            dept_code,
            prior_spec,
            current_spec,
        ) in TEST_ACCOUNTS_2627:
            student, s_created = Student.objects.get_or_create(
                ine=ine,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "gender": gender,
                    "nationality": france,
                },
            )
            if s_created:
                created_count += 1

            dept = dept_map[dept_code]
            profile = "nouveau"
            if prior_spec is not None:
                profile = "ancien"
                if self._get_or_create_enrollment(
                    student, prior_year, dept, level_map, prior_spec
                ):
                    created_count += 1

            level_code, is_alternant, is_scholarship, _gpa = current_spec
            if self._get_or_create_enrollment(
                student, year, dept, level_map, current_spec
            ):
                created_count += 1

            self.stdout.write(
                f"  {ine} — {first} {last} ({dept_code}, {profile}, "
                f"{'FISA' if is_alternant else 'FISE'}, "
                f"{'boursier' if is_scholarship else 'non boursier'})"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(TEST_ACCOUNTS_2627)} compte(s) de test 2026-2027 vérifié(s), "
                f"{created_count} enregistrement(s) créé(s)."
            )
        )
