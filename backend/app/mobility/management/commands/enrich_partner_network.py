"""
Enrichit le réseau de partenaires (universités, accords, cadres de mobilité)
de façon strictement additive : ne modifie ni ne supprime jamais une ligne
existante, se contente d'ajouter ce qui manque.

Contexte : contrairement à `reset_historical_years` (qui vide et reconstruit
les données liées aux années), cette commande est volontairement non
destructive — pensée pour enrichir une base qui contient déjà des données
réelles ou générées qu'on ne veut pas perdre (étudiants, vœux, affectations).

Détection des doublons : par nom exact (`PartnerUniversity.name`,
`Agreement.name`) via `get_or_create`. Une université déjà présente sous un
nom légèrement différent (ex. accents, abréviation) ne sera pas fusionnée —
volontairement, pour ne jamais risquer de faire pointer un accord existant
vers la mauvaise ligne. Idempotent : relancer la commande ne recrée rien.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

# (name, short_name, translated_name, erasmus_code, city, country_iso2)
# Les noms marqués (*) reprennent volontairement l'orthographe déjà présente
# en base (vue en pratique sur cette instance) pour rattacher l'accord à
# l'université existante plutôt que d'en créer une quasi-doublon.
UNIVERSITIES = [
    (
        "Technische Universitat Munchen",
        "TUM",
        "Universite Technique de Munich",
        "D MUNCHEN02",
        "Munich",
        "DE",
    ),
    (
        "Universidad Politecnica de Madrid",
        "UPM",
        "Universite Polytechnique de Madrid",
        "E MADRID05",
        "Madrid",
        "ES",
    ),
    ("ETH Zurich", "ETH", "Ecole Polytechnique Federale de Zurich", "", "Zurich", "CH"),
    ("McGill University", "McGill", "Universite McGill", "", "Montreal", "CA"),
    (
        "Politecnico di Milano",
        "Polimi",
        "Ecole Polytechnique de Milan",
        "I MILANO006",
        "Milan",
        "IT",
    ),
    (
        "Delft University of Technology",
        "TU Delft",
        "Univ. de Technologie de Delft",
        "NL DELFT01",
        "Delft",
        "NL",
    ),
    (
        "KTH Royal Institute of Technology",
        "KTH",
        "Institut Royal de Technologie de Stockholm",
        "S STOCKHO03",
        "Stockholm",
        "SE",
    ),
    (
        "Imperial College London",
        "Imperial",
        "Imperial College de Londres",
        "",
        "Londres",
        "GB",
    ),  # (*) existe déjà
    ("University of Tokyo", "UTokyo", "Universite de Tokyo", "", "Tokyo", "JP"),
    (
        "Instituto Superior Técnico",
        "IST Lisboa",
        "Institut Superieur Technique de Lisbonne",
        "P LISBOA03",
        "Lisbonne",
        "PT",
    ),  # (*)
    (
        "Technical University of Denmark",
        "DTU",
        "Universite Technique du Danemark",
        "DK LYNGBY01",
        "Lyngby",
        "DK",
    ),
    (
        "NTNU Trondheim",
        "NTNU",
        "Universite Norvegienne de Sciences et Technologie",
        "N TRONDHE01",
        "Trondheim",
        "NO",
    ),  # (*) existe déjà
    (
        "University of Melbourne",
        "Melbourne",
        "Universite de Melbourne",
        "",
        "Melbourne",
        "AU",
    ),
    (
        "Korea Advanced Institute of Science and Technology",
        "KAIST",
        "Institut Coreen des Sciences et Technologies Avancees",
        "",
        "Daejeon",
        "KR",
    ),
    (
        "National University of Singapore",
        "NUS",
        "Universite Nationale de Singapour",
        "",
        "Singapour",
        "SG",
    ),
    (
        "Vrije Universiteit Brussel",
        "VUB",
        "Universite Libre de Bruxelles (neerlandophone)",
        "B BRUSSEL04",
        "Bruxelles",
        "BE",
    ),
    (
        "Warsaw University of Technology",
        "WUT",
        "Universite Polytechnique de Varsovie",
        "PL WARSZAW02",
        "Varsovie",
        "PL",
    ),  # (*) existe déjà
    (
        "Chalmers University",
        "Chalmers",
        "Universite Technique Chalmers",
        "S GOTEBOR02",
        "Goteborg",
        "SE",
    ),  # (*) existe déjà
    (
        "RWTH Aachen",
        "RWTH Aachen",
        "Universite Technique RWTH d'Aix-la-Chapelle",
        "D AACHEN01",
        "Aix-la-Chapelle",
        "DE",
    ),  # (*) existe déjà
    (
        "Universitat Politecnica de Catalunya",
        "UPC Barcelona",
        "Universite Polytechnique de Catalogne",
        "E BARCELO03",
        "Barcelone",
        "ES",
    ),
    (
        "Georgia Institute of Technology",
        "Georgia Tech",
        "Institut de Technologie de Georgie",
        "",
        "Atlanta",
        "US",
    ),
    (
        "University of Toronto",
        "U Toronto",
        "Universite de Toronto",
        "",
        "Toronto",
        "CA",
    ),
    ("Tsinghua University", "Tsinghua", "Universite Tsinghua", "", "Pekin", "CN"),
    (
        "Indian Institute of Technology Bombay",
        "IIT Bombay",
        "Institut Indien de Technologie de Bombay",
        "",
        "Bombay",
        "IN",
    ),
    ("University of Cape Town", "UCT", "Universite du Cap", "", "Le Cap", "ZA"),
    (
        "Pontificia Universidad Catolica de Chile",
        "PUC Chile",
        "Universite Pontificale Catholique du Chili",
        "",
        "Santiago",
        "CL",
    ),
    (
        "Universidade de Sao Paulo",
        "USP",
        "Universite de Sao Paulo",
        "",
        "Sao Paulo",
        "BR",
    ),
    (
        "Czech Technical University in Prague",
        "CTU Prague",
        "Universite Technique Tcheque de Prague",
        "CZ PRAHA03",
        "Prague",
        "CZ",
    ),
    (
        "Budapest University of Technology and Economics",
        "BME",
        "Universite de Technologie et d'Economie de Budapest",
        "HU BUDAPES03",
        "Budapest",
        "HU",
    ),
    ("Aalto University", "Aalto", "Universite Aalto", "SF HELSINK04", "Espoo", "FI"),
    (
        "Trinity College Dublin",
        "TCD",
        "Trinity College de Dublin",
        "IRLDUBLIN01",
        "Dublin",
        "IE",
    ),
    (
        "Istanbul Technical University",
        "ITU",
        "Universite Technique d'Istanbul",
        "TR ISTANBU06",
        "Istanbul",
        "TR",
    ),
    (
        "King Abdullah University of Science and Technology",
        "KAUST",
        "Universite Roi Abdallah des Sciences et Technologies",
        "",
        "Thuwal",
        "SA",
    ),
    (
        "Universiti Teknologi Malaysia",
        "UTM",
        "Universite Technologique de Malaisie",
        "",
        "Johor Bahru",
        "MY",
    ),
    (
        "University of Auckland",
        "Auckland",
        "Universite d'Auckland",
        "",
        "Auckland",
        "NZ",
    ),
]

# (name, university_name, category_name, direction, valid_from, valid_until,
#  inp_total_places, inp_institutions, remarks, level_codes, dept_codes)
AGREEMENTS = [
    (
        "Erasmus+ TU Munchen",
        "Technische Universitat Munchen",
        "Erasmus",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        4,
        "INP Toulouse",
        "",
        ["2ING", "3ING"],
        ["SN", "3EA"],
    ),
    (
        "Erasmus+ UPM Madrid",
        "Universidad Politecnica de Madrid",
        "Erasmus",
        "outgoing",
        "2019-09-01",
        "2026-08-31",
        3,
        "INP Toulouse",
        "",
        ["2M", "2ING"],
        ["SN"],
    ),
    (
        "Convention ETH Zurich",
        "ETH Zurich",
        "Exchange",
        "outgoing",
        "2021-09-01",
        "2026-08-31",
        2,
        "ENSEEIHT",
        "",
        ["2ING", "3ING"],
        ["3EA", "MF2E"],
    ),
    (
        "Convention McGill",
        "McGill University",
        "Exchange",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        2,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2M", "2ING", "3ING"],
        ["SN"],
    ),
    (
        "Erasmus+ Politecnico di Milano",
        "Politecnico di Milano",
        "Erasmus",
        "outgoing",
        "2018-09-01",
        "2028-08-31",
        5,
        "INP Toulouse",
        "",
        ["2M", "2ING", "3ING"],
        ["SN", "3EA", "MF2E"],
    ),
    (
        "Erasmus+ TU Delft",
        "Delft University of Technology",
        "Erasmus",
        "outgoing",
        "2022-09-01",
        "2027-08-31",
        2,
        "ENSEEIHT",
        "Nouvel accord signe en 2022",
        ["2ING", "3ING"],
        ["3EA"],
    ),
    (
        "Erasmus+ KTH Stockholm",
        "KTH Royal Institute of Technology",
        "Erasmus",
        "outgoing",
        "2024-09-01",
        "2029-08-31",
        3,
        "INP Toulouse",
        "Nouvel accord signe en 2024",
        ["2ING", "3ING"],
        ["SN", "3EA"],
    ),
    (
        "Convention Imperial College London",
        "Imperial College London",
        "Exchange",
        "outgoing",
        "2019-09-01",
        "2026-08-31",
        3,
        "INP Toulouse",
        "Hors Erasmus depuis le Brexit",
        ["2ING", "3ING"],
        ["SN", "3EA"],
    ),
    (
        "Convention University of Tokyo",
        "University of Tokyo",
        "Exchange",
        "outgoing",
        "2021-09-01",
        "2027-08-31",
        2,
        "ENSEEIHT",
        "Hors Erasmus - financement etudiant",
        ["2ING", "3ING"],
        ["SN", "MF2E"],
    ),
    (
        "Erasmus+ IST Lisboa",
        "Instituto Superior Técnico",
        "Erasmus",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        2,
        "INP Toulouse",
        "",
        ["2M", "2ING"],
        ["3EA"],
    ),
    (
        "Erasmus+ DTU Lyngby",
        "Technical University of Denmark",
        "Erasmus",
        "outgoing",
        "2022-09-01",
        "2028-08-31",
        3,
        "INP Toulouse",
        "",
        ["2ING", "3ING"],
        ["SN", "MF2E"],
    ),
    (
        "Erasmus+ NTNU Trondheim",
        "NTNU Trondheim",
        "Erasmus",
        "outgoing",
        "2023-09-01",
        "2028-08-31",
        2,
        "ENSEEIHT",
        "Nouvel accord signe en 2023",
        ["2ING", "3ING"],
        ["MF2E"],
    ),
    (
        "Convention University of Melbourne",
        "University of Melbourne",
        "Exchange",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        2,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2M", "2ING", "3ING"],
        ["SN", "3EA", "MF2E"],
    ),
    (
        "Convention KAIST",
        "Korea Advanced Institute of Science and Technology",
        "Exchange",
        "outgoing",
        "2021-09-01",
        "2026-08-31",
        2,
        "ENSEEIHT",
        "Hors Erasmus - financement etudiant",
        ["2M", "2ING"],
        ["SN"],
    ),
    (
        "Convention NUS Singapour",
        "National University of Singapore",
        "Exchange",
        "outgoing",
        "2022-09-01",
        "2027-08-31",
        2,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2M", "2ING", "3ING"],
        ["SN", "3EA"],
    ),
    (
        "Erasmus+ VUB Bruxelles",
        "Vrije Universiteit Brussel",
        "Erasmus",
        "outgoing",
        "2019-09-01",
        "2026-08-31",
        2,
        "INP Toulouse",
        "",
        ["2ING", "3ING"],
        ["3EA"],
    ),
    (
        "Erasmus+ Warsaw Univ. of Tech.",
        "Warsaw University of Technology",
        "Erasmus",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        3,
        "ENSEEIHT",
        "",
        ["2ING", "3ING"],
        ["MF2E"],
    ),
    (
        "Erasmus+ Chalmers Goteborg",
        "Chalmers University",
        "Erasmus",
        "outgoing",
        "2018-09-01",
        "2028-08-31",
        3,
        "INP Toulouse",
        "",
        ["2M", "2ING", "3ING"],
        ["3EA", "MF2E"],
    ),
    (
        "Erasmus+ RWTH Aachen",
        "RWTH Aachen",
        "Erasmus",
        "outgoing",
        "2019-09-01",
        "2026-08-31",
        4,
        "INP Toulouse",
        "",
        ["2ING", "3ING"],
        ["SN", "3EA"],
    ),
    (
        "Erasmus+ UPC Barcelone",
        "Universitat Politecnica de Catalunya",
        "Erasmus",
        "outgoing",
        "2021-09-01",
        "2028-08-31",
        3,
        "ENSEEIHT",
        "",
        ["2M", "2ING", "3ING"],
        ["SN", "MF2E"],
    ),
    (
        "Convention Georgia Tech (Exchange)",
        "Georgia Institute of Technology",
        "Exchange",
        "outgoing",
        "2019-09-01",
        "2026-08-31",
        2,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2ING", "3ING"],
        ["SN", "3EA"],
    ),
    (
        "Convention University of Toronto",
        "University of Toronto",
        "Exchange",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        2,
        "ENSEEIHT",
        "Hors Erasmus - financement etudiant",
        ["2ING", "3ING"],
        ["3EA"],
    ),
    (
        "Convention Tsinghua University",
        "Tsinghua University",
        "Exchange",
        "outgoing",
        "2021-09-01",
        "2028-08-31",
        2,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2M", "2ING", "3ING"],
        ["SN"],
    ),
    (
        "Convention IIT Bombay",
        "Indian Institute of Technology Bombay",
        "Exchange",
        "outgoing",
        "2022-09-01",
        "2027-08-31",
        2,
        "ENSEEIHT",
        "Hors Erasmus - financement etudiant",
        ["2ING", "3ING"],
        ["3EA", "MF2E"],
    ),
    (
        "Convention University of Cape Town",
        "University of Cape Town",
        "Exchange",
        "outgoing",
        "2020-09-01",
        "2026-08-31",
        2,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2ING", "3ING"],
        ["SN"],
    ),
    (
        "Convention PUC Chile",
        "Pontificia Universidad Catolica de Chile",
        "Exchange",
        "outgoing",
        "2021-09-01",
        "2027-08-31",
        2,
        "ENSEEIHT",
        "Hors Erasmus - financement etudiant",
        ["2ING", "3ING"],
        ["3EA"],
    ),
    (
        "Convention USP Sao Paulo",
        "Universidade de Sao Paulo",
        "Exchange",
        "outgoing",
        "2019-09-01",
        "2026-08-31",
        2,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2M", "2ING", "3ING"],
        ["MF2E"],
    ),
    (
        "Erasmus+ CTU Prague",
        "Czech Technical University in Prague",
        "Erasmus",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        3,
        "ENSEEIHT",
        "",
        ["2ING", "3ING"],
        ["SN"],
    ),
    (
        "Erasmus+ BME Budapest",
        "Budapest University of Technology and Economics",
        "Erasmus",
        "outgoing",
        "2021-09-01",
        "2028-08-31",
        2,
        "INP Toulouse",
        "",
        ["2ING", "3ING"],
        ["3EA"],
    ),
    (
        "Erasmus+ Aalto University",
        "Aalto University",
        "Erasmus",
        "outgoing",
        "2022-09-01",
        "2027-08-31",
        3,
        "ENSEEIHT",
        "",
        ["2M", "2ING", "3ING"],
        ["SN", "MF2E"],
    ),
    (
        "Erasmus+ Trinity College Dublin",
        "Trinity College Dublin",
        "Erasmus",
        "outgoing",
        "2019-09-01",
        "2026-08-31",
        2,
        "INP Toulouse",
        "",
        ["2ING", "3ING"],
        ["3EA"],
    ),
    (
        "Erasmus+ Istanbul Tech. Univ.",
        "Istanbul Technical University",
        "Erasmus",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        3,
        "ENSEEIHT",
        "",
        ["2ING", "3ING"],
        ["MF2E"],
    ),
    (
        "Convention KAUST",
        "King Abdullah University of Science and Technology",
        "Exchange",
        "outgoing",
        "2022-09-01",
        "2028-08-31",
        1,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2M", "2ING"],
        ["SN"],
    ),
    (
        "Convention UTM Malaysia",
        "Universiti Teknologi Malaysia",
        "Exchange",
        "outgoing",
        "2021-09-01",
        "2027-08-31",
        2,
        "ENSEEIHT",
        "Hors Erasmus - financement etudiant",
        ["2ING", "3ING"],
        ["3EA"],
    ),
    (
        "Convention University of Auckland",
        "University of Auckland",
        "Exchange",
        "outgoing",
        "2020-09-01",
        "2026-08-31",
        2,
        "INP Toulouse",
        "Hors Erasmus - financement etudiant",
        ["2ING", "3ING"],
        ["MF2E"],
    ),
    (
        "Double diplome TU Munchen",
        "Technische Universitat Munchen",
        "DD",
        "outgoing",
        "2021-09-01",
        "2028-08-31",
        2,
        "INP Toulouse",
        "Double diplome ingenieur",
        ["3ING"],
        ["SN"],
    ),
    (
        "Double diplome RWTH Aachen",
        "RWTH Aachen",
        "DD",
        "outgoing",
        "2020-09-01",
        "2027-08-31",
        2,
        "ENSEEIHT",
        "Double diplome ingenieur",
        ["3ING"],
        ["SN", "3EA"],
    ),
    (
        "Double diplome Politecnico di Milano",
        "Politecnico di Milano",
        "DD",
        "outgoing",
        "2019-09-01",
        "2026-08-31",
        2,
        "INP Toulouse",
        "Double diplome ingenieur",
        ["3ING"],
        ["MF2E"],
    ),
    (
        "Double diplome UPC Barcelone",
        "Universitat Politecnica de Catalunya",
        "DD",
        "outgoing",
        "2022-09-01",
        "2029-08-31",
        1,
        "ENSEEIHT",
        "Double diplome ingenieur",
        ["3ING"],
        ["SN"],
    ),
    (
        "Double diplome Georgia Tech",
        "Georgia Institute of Technology",
        "DD",
        "outgoing",
        "2021-09-01",
        "2028-08-31",
        1,
        "INP Toulouse",
        "Double diplome ingenieur",
        ["3ING"],
        ["3EA"],
    ),
]


class Command(BaseCommand):
    help = (
        "Enrichit universités partenaires / accords / cadres de mobilité de "
        "façon additive (get_or_create par nom) — ne touche jamais aux "
        "lignes existantes."
    )

    def handle(self, *args, **options):
        from app.institutions.models import PartnerUniversity
        from app.mobility.models import Agreement, AgreementDepartment, MobilityCategory
        from app.reference.models import Country, Department, Level

        with transaction.atomic():
            univ_created = 0
            for name, short, translated, code, city, iso2 in UNIVERSITIES:
                country = Country.objects.filter(iso2=iso2).first()
                if country is None:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Pays inconnu ({iso2}) pour {name} — ignoré"
                        )
                    )
                    continue
                _, created = PartnerUniversity.objects.get_or_create(
                    name=name,
                    defaults={
                        "short_name": short,
                        "translated_name": translated,
                        "erasmus_code": code,
                        "city": city,
                        "country": country,
                    },
                )
                univ_created += int(created)
            self.stdout.write(
                f"Universités partenaires : {univ_created} créées "
                f"(sur {len(UNIVERSITIES)} visées, le reste existait déjà)"
            )

            cat_cache: dict[str, MobilityCategory] = {}

            def get_category(name: str) -> MobilityCategory:
                if name not in cat_cache:
                    cat_cache[name], _ = MobilityCategory.objects.get_or_create(
                        name=name
                    )
                return cat_cache[name]

            dept_cache = {d.code: d for d in Department.objects.all()}
            level_cache = {lv.code: lv for lv in Level.objects.all()}

            ag_created = 0
            agdept_created = 0
            for (
                name,
                univ_name,
                cat_name,
                direction,
                valid_from,
                valid_until,
                places,
                institutions,
                remarks,
                level_codes,
                dept_codes,
            ) in AGREEMENTS:
                univ = PartnerUniversity.objects.filter(name=univ_name).first()
                if univ is None:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Université introuvable ({univ_name}) pour l'accord "
                            f"{name} — ignoré"
                        )
                    )
                    continue

                agreement, created = Agreement.objects.get_or_create(
                    name=name,
                    defaults={
                        "partner_university": univ,
                        "category": get_category(cat_name),
                        "direction": direction,
                        "valid_from": valid_from,
                        "valid_until": valid_until,
                        "inp_total_places": places,
                        "inp_institutions": institutions,
                        "remarks": remarks,
                    },
                )
                if not created:
                    continue
                ag_created += 1

                levels = [level_cache[c] for c in level_codes if c in level_cache]
                agreement.levels.set(levels)

                for dept_code in dept_codes:
                    dept = dept_cache.get(dept_code)
                    if dept is None:
                        continue
                    _, ad_created = AgreementDepartment.objects.get_or_create(
                        agreement=agreement, department=dept
                    )
                    agdept_created += int(ad_created)

            self.stdout.write(
                f"Accords : {ag_created} créés (sur {len(AGREEMENTS)} visés, "
                f"le reste existait déjà par nom)"
            )
            self.stdout.write(
                f"Rattachements accord-département : {agdept_created} créés"
            )

        self.stdout.write(
            self.style.SUCCESS("\n✓ Enrichissement du réseau partenaire terminé.")
        )
