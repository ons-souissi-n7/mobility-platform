"""
Génération d'étudiants/vœux de démonstration, partagée entre
`reset_historical_years` (construction d'une année depuis zéro) et
`topup_historical_years` (ajout d'un lot à une année déjà existante) — les
deux commandes utilisaient auparavant deux copies de cette même logique, avec
le risque qu'un ajustement (plage de GPA, probabilités alternant/boursier,
politique d'échantillonnage des vœux) ne soit fait que dans l'une des deux.

Préfixé `_` : ce n'est pas une commande Django (pas de classe `Command`), le
loader de `manage.py` l'ignore donc silencieusement.

`random` sert uniquement à générer des étudiants/vœux de démonstration
plausibles (jamais un token, un mot de passe ou une décision de sécurité).
Sans objet pour les hotspots Sonar "pseudorandom number generator" (S2245).
"""

import random
from collections.abc import Callable

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

# Échelle française /20 (cf. StudentProfileOut, chapitre 4 du rapport) —
# jamais 0-4 : le moteur de recommandation entraîne son StandardScaler sur
# ces valeurs, une mauvaise échelle ici corrompt silencieusement le scoring
# des vrais étudiants.
GPA_RANGE = (10.0, 18.0)


def create_demo_students(
    year,
    depts,
    levels_by_code,
    parcours_by_dept,
    countries,
    n_per_dept: int,
    ine_start_index: Callable[[object], int] = lambda dept: 1,
) -> list:
    """Crée `n_per_dept` AnnualEnrollment (+ Student) par département pour
    `year`. `ine_start_index(dept)` fixe l'indice de départ du INE pour ce
    département — 1 par défaut (nouvelle année), ou une fonction qui repart
    après le plus haut indice déjà utilisé (ajout à une année existante,
    cf. topup_historical_years)."""
    from app.students.models import AnnualEnrollment, GenderChoice, Student

    start_year = year.start_date.year
    enrollments = []
    for dept in depts:
        parcours_list = parcours_by_dept.get(dept.code, [])
        start_index = ine_start_index(dept)
        for i in range(start_index, start_index + n_per_dept):
            is_female = random.random() < 0.45  # NOSONAR (S2245) — donnée de démo
            first = random.choice(  # NOSONAR (S2245) — donnée de démo
                FIRST_NAMES_F if is_female else FIRST_NAMES_M
            )
            last = random.choice(LAST_NAMES)  # NOSONAR (S2245) — donnée de démo
            ine = f"{start_year}{dept.code}{i:03d}"
            if Student.objects.filter(ine=ine).exists():
                continue
            iso2 = random.choice(NATIONALITY_POOL)  # NOSONAR (S2245) — donnée de démo
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
                random.uniform(*GPA_RANGE),
                2,  # NOSONAR (S2245) — donnée de démo
            )
            enrollment = AnnualEnrollment.objects.create(
                student=student,
                academic_year=year,
                department=dept,
                level=level,
                parcours=parcours_choice,
                gpa=gpa_value,
                is_alternant=random.random() < 0.25,  # NOSONAR (S2245)
                is_scholarship=random.random() < 0.2,  # NOSONAR (S2245)
            )
            enrollments.append(enrollment)
    return enrollments


def create_demo_wishes(enrollments, dept_to_ays: dict) -> int:
    """Crée 1 à 3 vœux par inscription parmi les AgreementYear éligibles
    (`dept_to_ays[dept_code]` = liste de `(AgreementYear, allowed_level_ids)`)."""
    from app.students.models import StudentWish

    created = 0
    for enrollment in enrollments:
        eligible = [
            ay
            for ay, allowed_level_ids in dept_to_ays.get(enrollment.department.code, [])
            if not allowed_level_ids or enrollment.level_id in allowed_level_ids
        ]
        if not eligible:
            continue
        n = min(len(eligible), random.randint(1, 3))  # NOSONAR (S2245)
        chosen = random.sample(eligible, n)  # NOSONAR (S2245) — donnée de démo
        for rank, ay in enumerate(chosen, start=1):
            StudentWish.objects.create(
                annual_enrollment=enrollment, agreement_year=ay, rank=rank
            )
            created += 1
    return created
