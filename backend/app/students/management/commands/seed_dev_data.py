"""
Seed données de développement — année 2025-2026.

Prérequis (fixtures déjà chargées dans la DB) :
  - Départements  : SN pk=13, 3EA pk=14, MF2E pk=15
  - Niveaux       : 2ING pk=5 (FISE), 3ING pk=7 (FISA)
  - Accords       : 7 accords pk=1-7 (chargés via loaddata agreements)
  - Année 2025-2026 : pk=4, statut quelconque

Ce que le script crée :
  - 5 nouveaux accords de mobilité (EPFL, TU Berlin, Politecnico Torino, Imperial, Lund)
  - AgreementYears 2025-2026 pour tous les accords (12 au total)
  - AgreementYearDepartments (quotas par département)
  - 55 étudiants (35 FISE 2ING + 20 FISA 3ING), mix français/internationaux
  - GPA sur échelle 0–4
  - Vœux contrôlés : 3 étudiants MF2E souhaitent des accords sans quota MF2E
    → l'algo leur attribuera une destination alternative (slot_type=alternative)
  - Affectations historiques publiées pour 2022-2025

Idempotent : peut être relancé plusieurs fois sans doublons.
"""

import random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# ── Quotas pour les accords existants (AgreementYears 2025-2026) ──────────────
# (agreement_name, {dept_code: estimated_places}, n7_places)
EXISTING_AGREEMENT_QUOTAS_2526 = [
    ("Erasmus+ TU Munchen", {"SN": 3, "3EA": 2}, 5),
    ("Erasmus+ UPM Madrid", {"SN": 2, "MF2E": 2}, 4),
    ("Convention ETH Zurich", {"3EA": 2, "MF2E": 2}, 4),
    ("Convention McGill", {"SN": 2, "3EA": 1}, 3),
    ("Erasmus+ Politecnico di Milano", {"SN": 2, "3EA": 2, "MF2E": 2}, 6),
    ("Erasmus+ TU Delft", {"3EA": 2, "MF2E": 2}, 4),
    ("Erasmus+ KTH Stockholm", {"SN": 2, "3EA": 2}, 4),
]

# ── Nouveaux accords à créer si absents ──────────────────────────────────────
# (agreement_name, university_name, country_iso2, category_name,
#  {dept_code: estimated_places}, n7_places)
NEW_AGREEMENTS_DATA = [
    (
        "Convention EPFL Lausanne",
        "EPFL",
        "CH",
        "Exchange",
        {"SN": 2, "MF2E": 2},
        4,
    ),
    (
        "Erasmus+ TU Berlin",
        "Technische Universitat Berlin",
        "DE",
        "Erasmus",
        {"SN": 2, "3EA": 2},
        4,
    ),
    (
        "Erasmus+ Politecnico Torino",
        "Politecnico di Torino",
        "IT",
        "Erasmus",
        {"3EA": 2, "MF2E": 2},
        4,
    ),
    (
        "Convention Imperial College",
        "Imperial College London",
        "GB",
        "DD",
        {"SN": 1, "3EA": 1},
        2,
    ),
    (
        "Convention Lund University",
        "Lund University",
        "SE",
        "Exchange",
        {"SN": 1, "3EA": 1, "MF2E": 1},
        3,
    ),
]

ALL_AGREEMENT_NAMES = [a[0] for a in EXISTING_AGREEMENT_QUOTAS_2526] + [
    a[0] for a in NEW_AGREEMENTS_DATA
]

# Quotas combinés : accords existants + nouveaux (pour _ensure_agreement_year_departments)
ALL_AGREEMENT_QUOTAS_2526 = EXISTING_AGREEMENT_QUOTAS_2526 + [
    (name, dept_quotas, n7_places)
    for name, _univ, _country, _cat, dept_quotas, n7_places in NEW_AGREEMENTS_DATA
]

# ── Étudiants boursiers ───────────────────────────────────────────────────────
SCHOLARSHIP_INES: set[str] = {
    "20SN002FISE",
    "20SN007FISE",
    "20SN013FISE",
    "203EA04FISE",
    "203EA09FISE",
    "20MF203FISE",
    "20MF208FISE",
    "20SN003FISA",
    "203EA06FISA",
    "20MF204FISA",
    "20MF205FISA",
}

# ── Vœux imposés pour certains étudiants MF2E ─────────────────────────────────
# Ces 3 étudiants MF2E souhaitent des accords qui N'ONT PAS de quota MF2E.
# Résultat attendu : rejetés de leurs vœux → affectés en destination alternative.
FORCED_WISHES: dict[str, list[str]] = {
    "20MF204FISE": [
        "Erasmus+ TU Munchen",
        "Erasmus+ KTH Stockholm",
        "Convention McGill",
    ],
    "20MF209FISE": [
        "Erasmus+ TU Munchen",
        "Erasmus+ KTH Stockholm",
        "Convention McGill",
    ],
    "20MF202FISA": [
        "Erasmus+ TU Munchen",
        "Erasmus+ KTH Stockholm",
        "Convention McGill",
    ],
}

# ── FISE 2ING ─────────────────────────────────────────────────────────────────
FISE_STUDENTS = [
    # ── SN ──
    (
        "Alexandre",
        "MARTIN",
        "20SN001FISE",
        "a.martin@etu.inp-toulouse.fr",
        "M",
        "FR",
        "SN",
        3.65,
    ),
    (
        "Léa",
        "DUPONT",
        "20SN002FISE",
        "l.dupont@etu.inp-toulouse.fr",
        "F",
        "FR",
        "SN",
        3.82,
    ),
    (
        "Nicolas",
        "BERNARD",
        "20SN003FISE",
        "n.bernard@etu.inp-toulouse.fr",
        "M",
        "FR",
        "SN",
        3.10,
    ),
    (
        "Camille",
        "PETIT",
        "20SN004FISE",
        "c.petit@etu.inp-toulouse.fr",
        "F",
        "FR",
        "SN",
        3.45,
    ),
    (
        "Julien",
        "MOREAU",
        "20SN005FISE",
        "j.moreau@etu.inp-toulouse.fr",
        "M",
        "FR",
        "SN",
        2.90,
    ),
    (
        "Sophie",
        "LAURENT",
        "20SN006FISE",
        "s.laurent@etu.inp-toulouse.fr",
        "F",
        "FR",
        "SN",
        3.95,
    ),
    (
        "Maxime",
        "SIMON",
        "20SN007FISE",
        "m.simon@etu.inp-toulouse.fr",
        "M",
        "FR",
        "SN",
        2.70,
    ),
    (
        "Lucie",
        "MICHEL",
        "20SN008FISE",
        "l.michel@etu.inp-toulouse.fr",
        "F",
        "FR",
        "SN",
        3.50,
    ),
    (
        "Lucas",
        "PIRES",
        "20SN009FISE",
        "l.pires@etu.inp-toulouse.fr",
        "M",
        "FR",
        "SN",
        3.20,
    ),
    (
        "Clara",
        "ARNAUD",
        "20SN010FISE",
        "c.arnaud@etu.inp-toulouse.fr",
        "F",
        "FR",
        "SN",
        2.80,
    ),
    (
        "Carlos",
        "GARCIA",
        "20SN011FISE",
        "c.garcia@etu.inp-toulouse.fr",
        "M",
        "ES",
        "SN",
        3.35,
    ),
    (
        "Yuki",
        "TANAKA",
        "20SN012FISE",
        "y.tanaka@etu.inp-toulouse.fr",
        "F",
        "JP",
        "SN",
        3.78,
    ),
    (
        "Mehdi",
        "EL FASSI",
        "20SN013FISE",
        "m.elfassi@etu.inp-toulouse.fr",
        "M",
        "MA",
        "SN",
        3.05,
    ),
    (
        "Ana",
        "SILVA",
        "20SN014FISE",
        "a.silva@etu.inp-toulouse.fr",
        "F",
        "PT",
        "SN",
        3.40,
    ),
    # ── 3EA ──
    (
        "Thomas",
        "LEROY",
        "203EA01FISE",
        "t.leroy@etu.inp-toulouse.fr",
        "M",
        "FR",
        "3EA",
        3.55,
    ),
    (
        "Marie",
        "DUBOIS",
        "203EA02FISE",
        "m.dubois@etu.inp-toulouse.fr",
        "F",
        "FR",
        "3EA",
        3.70,
    ),
    (
        "Antoine",
        "GAUTHIER",
        "203EA03FISE",
        "a.gauthier@etu.inp-toulouse.fr",
        "M",
        "FR",
        "3EA",
        3.85,
    ),
    (
        "Claire",
        "ROUSSEAU",
        "203EA04FISE",
        "c.rousseau@etu.inp-toulouse.fr",
        "F",
        "FR",
        "3EA",
        3.00,
    ),
    (
        "Romain",
        "FONTAINE",
        "203EA05FISE",
        "r.fontaine@etu.inp-toulouse.fr",
        "M",
        "FR",
        "3EA",
        2.85,
    ),
    (
        "Elisa",
        "VINCENT",
        "203EA06FISE",
        "e.vincent@etu.inp-toulouse.fr",
        "F",
        "FR",
        "3EA",
        3.25,
    ),
    (
        "Baptiste",
        "MERCIER",
        "203EA07FISE",
        "b.mercier@etu.inp-toulouse.fr",
        "M",
        "FR",
        "3EA",
        3.75,
    ),
    (
        "Valentin",
        "PICARD",
        "203EA08FISE",
        "v.picard@etu.inp-toulouse.fr",
        "M",
        "FR",
        "3EA",
        3.15,
    ),
    (
        "Jan",
        "KOWALSKI",
        "203EA09FISE",
        "j.kowalski@etu.inp-toulouse.fr",
        "M",
        "PL",
        "3EA",
        3.20,
    ),
    (
        "Emma",
        "MULLER",
        "203EA10FISE",
        "e.muller@etu.inp-toulouse.fr",
        "F",
        "DE",
        "3EA",
        3.60,
    ),
    (
        "Omar",
        "BENNANI",
        "203EA11FISE",
        "o.bennani@etu.inp-toulouse.fr",
        "M",
        "MA",
        "3EA",
        2.95,
    ),
    (
        "Elena",
        "POPESCU",
        "203EA12FISE",
        "e.popescu@etu.inp-toulouse.fr",
        "F",
        "PL",
        "3EA",
        3.30,
    ),
    # ── MF2E ──
    (
        "Pierre",
        "BONNET",
        "20MF201FISE",
        "p.bonnet@etu.inp-toulouse.fr",
        "M",
        "FR",
        "MF2E",
        3.40,
    ),
    (
        "Julie",
        "LEBRUN",
        "20MF202FISE",
        "j.lebrun@etu.inp-toulouse.fr",
        "F",
        "FR",
        "MF2E",
        3.10,
    ),
    (
        "Florian",
        "MASSON",
        "20MF203FISE",
        "f.masson@etu.inp-toulouse.fr",
        "M",
        "FR",
        "MF2E",
        3.60,
    ),
    (
        "Aurélie",
        "CARON",
        "20MF204FISE",
        "a.caron@etu.inp-toulouse.fr",
        "F",
        "FR",
        "MF2E",
        2.75,
    ),
    (
        "Kevin",
        "RENARD",
        "20MF205FISE",
        "k.renard@etu.inp-toulouse.fr",
        "M",
        "FR",
        "MF2E",
        3.80,
    ),
    (
        "Manon",
        "GIRARD",
        "20MF206FISE",
        "m.girard@etu.inp-toulouse.fr",
        "F",
        "FR",
        "MF2E",
        3.25,
    ),
    (
        "Marco",
        "BIANCHI",
        "20MF207FISE",
        "m.bianchi@etu.inp-toulouse.fr",
        "M",
        "IT",
        "MF2E",
        3.15,
    ),
    (
        "Astrid",
        "HANSEN",
        "20MF208FISE",
        "a.hansen@etu.inp-toulouse.fr",
        "F",
        "DK",
        "MF2E",
        3.55,
    ),
    (
        "Ricardo",
        "GOMES",
        "20MF209FISE",
        "r.gomes@etu.inp-toulouse.fr",
        "M",
        "PT",
        "MF2E",
        2.90,
    ),
]

# ── FISA 3ING ─────────────────────────────────────────────────────────────────
FISA_STUDENTS = [
    # ── SN ──
    (
        "Thibault",
        "VIDAL",
        "20SN001FISA",
        "t.vidal@etu.inp-toulouse.fr",
        "M",
        "FR",
        "SN",
        3.55,
    ),
    (
        "Amina",
        "OUALI",
        "20SN002FISA",
        "a.ouali@etu.inp-toulouse.fr",
        "F",
        "FR",
        "SN",
        3.88,
    ),
    (
        "Théo",
        "FAURE",
        "20SN003FISA",
        "t.faure@etu.inp-toulouse.fr",
        "M",
        "FR",
        "SN",
        2.95,
    ),
    (
        "Pauline",
        "NOEL",
        "20SN004FISA",
        "p.noel@etu.inp-toulouse.fr",
        "F",
        "FR",
        "SN",
        3.30,
    ),
    (
        "Alexis",
        "LEFEBVRE",
        "20SN005FISA",
        "a.lefebvre@etu.inp-toulouse.fr",
        "M",
        "FR",
        "SN",
        3.70,
    ),
    (
        "Lars",
        "SVENSSON",
        "20SN006FISA",
        "l.svensson@etu.inp-toulouse.fr",
        "M",
        "SE",
        "SN",
        3.45,
    ),
    (
        "Fatima",
        "AL-HASSAN",
        "20SN007FISA",
        "f.alhassan@etu.inp-toulouse.fr",
        "F",
        "MA",
        "SN",
        3.10,
    ),
    # ── 3EA ──
    (
        "Quentin",
        "BLANC",
        "203EA01FISA",
        "q.blanc@etu.inp-toulouse.fr",
        "M",
        "FR",
        "3EA",
        3.25,
    ),
    (
        "Chloé",
        "MORIN",
        "203EA02FISA",
        "c.morin@etu.inp-toulouse.fr",
        "F",
        "FR",
        "3EA",
        3.60,
    ),
    (
        "Sébastien",
        "PERRIN",
        "203EA03FISA",
        "s.perrin@etu.inp-toulouse.fr",
        "M",
        "FR",
        "3EA",
        2.85,
    ),
    (
        "Anaïs",
        "DUPUIS",
        "203EA04FISA",
        "a.dupuis@etu.inp-toulouse.fr",
        "F",
        "FR",
        "3EA",
        3.00,
    ),
    (
        "Mathieu",
        "GARNIER",
        "203EA05FISA",
        "m.garnier@etu.inp-toulouse.fr",
        "M",
        "FR",
        "3EA",
        3.75,
    ),
    (
        "Tomás",
        "LOPEZ",
        "203EA06FISA",
        "t.lopez@etu.inp-toulouse.fr",
        "M",
        "ES",
        "3EA",
        3.20,
    ),
    (
        "Ingrid",
        "LARSEN",
        "203EA07FISA",
        "i.larsen@etu.inp-toulouse.fr",
        "F",
        "NO",
        "3EA",
        3.50,
    ),
    (
        "David",
        "CHEN",
        "203EA08FISA",
        "d.chen@etu.inp-toulouse.fr",
        "M",
        "CA",
        "3EA",
        3.40,
    ),
    # ── MF2E ──
    (
        "Tristan",
        "POULAIN",
        "20MF201FISA",
        "t.poulain@etu.inp-toulouse.fr",
        "M",
        "FR",
        "MF2E",
        3.35,
    ),
    (
        "Océane",
        "RENAULT",
        "20MF202FISA",
        "o.renault@etu.inp-toulouse.fr",
        "F",
        "FR",
        "MF2E",
        2.80,
    ),
    (
        "Rémi",
        "TESSIER",
        "20MF203FISA",
        "r.tessier@etu.inp-toulouse.fr",
        "M",
        "FR",
        "MF2E",
        3.60,
    ),
    (
        "Nadia",
        "BENALI",
        "20MF204FISA",
        "n.benali@etu.inp-toulouse.fr",
        "F",
        "MA",
        "MF2E",
        2.95,
    ),
    (
        "Pietro",
        "ROSSI",
        "20MF205FISA",
        "p.rossi@etu.inp-toulouse.fr",
        "M",
        "IT",
        "MF2E",
        3.10,
    ),
]

ALL_STUDENTS = FISE_STUDENTS + FISA_STUDENTS


class Command(BaseCommand):
    help = "Seed la base avec des étudiants, vœux et affectations historiques pour 2025-2026"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Supprime les données créées par ce script avant de recréer",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        with transaction.atomic():
            self._check_prerequisites()
            current_year = self._load_current_year()
            dept_map = self._load_departments()
            level_2ing = self._load_level("2ING")
            level_3ing = self._load_level("3ING")
            country_map = self._load_countries()
            parcours_map = self._load_parcours()
            self._ensure_new_agreements(dept_map, country_map, current_year)
            self._ensure_agreement_year_departments(dept_map, current_year)
            enrollments = self._create_students_and_enrollments(
                dept_map,
                level_2ing,
                level_3ing,
                country_map,
                current_year,
                parcours_map,
            )
            self._create_wishes(enrollments, current_year)
            self._create_historical_assignments(
                dept_map, level_2ing, level_3ing, country_map, parcours_map
            )

        self.stdout.write(self.style.SUCCESS("\n✓ Seed terminé."))
        self.stdout.write(
            "  → Passe l'année en état 'import' puis lance POST /api/v1/academic/years/4/launch-assignment/ "
            "pour déclencher l'algorithme Gale-Shapley.\n"
            "  → 12 accords · ~59 places · 55 étudiants : résultat attendu ~85 % affectés."
        )

    # ────────────────────────────────────────────────────────────────────────
    # Flush
    # ────────────────────────────────────────────────────────────────────────

    def _flush(self):
        from app.mobility.models import AgreementYearDepartment
        from app.outgoing.models import Assignment, AssignmentResult
        from app.students.models import AnnualEnrollment, Student, StudentWish

        all_ines = [s[2] for s in ALL_STUDENTS]

        n = AssignmentResult.objects.filter(
            annual_enrollment__student__ine__in=all_ines
        ).delete()[0]
        self.stdout.write(f"  AssignmentResults supprimés : {n}")

        n = Assignment.objects.filter(run_by="seed_dev_data").delete()[0]
        self.stdout.write(f"  Assignments supprimés : {n}")

        n = StudentWish.objects.filter(
            annual_enrollment__student__ine__in=all_ines
        ).delete()[0]
        self.stdout.write(f"  Vœux supprimés : {n}")

        n = AnnualEnrollment.objects.filter(student__ine__in=all_ines).delete()[0]
        self.stdout.write(f"  Inscriptions supprimées : {n}")

        n = Student.objects.filter(ine__in=all_ines).delete()[0]
        self.stdout.write(f"  Étudiants supprimés : {n}")

        n = AgreementYearDepartment.objects.filter(
            agreement_year__academic_year__label="2025-2026"
        ).delete()[0]
        self.stdout.write(f"  AgreementYearDepartments 2025-2026 supprimés : {n}")

    # ────────────────────────────────────────────────────────────────────────
    # Prérequis
    # ────────────────────────────────────────────────────────────────────────

    def _check_prerequisites(self):
        from app.academic.models import AcademicYear
        from app.mobility.models import Agreement
        from app.reference.models import Department, Level

        for code in ("SN", "3EA", "MF2E"):
            if not Department.objects.filter(code=code).exists():
                raise CommandError(
                    f"Département '{code}' manquant. "
                    "Chargez d'abord : python manage.py loaddata departments"
                )
        for code in ("2ING", "3ING"):
            if not Level.objects.filter(code=code).exists():
                raise CommandError(
                    f"Niveau '{code}' manquant. "
                    "Chargez d'abord : python manage.py loaddata levels"
                )
        if not AcademicYear.objects.filter(label="2025-2026").exists():
            raise CommandError(
                "Année 2025-2026 absente. "
                "Chargez d'abord : python manage.py loaddata academic_years"
            )
        for name in [a[0] for a in EXISTING_AGREEMENT_QUOTAS_2526]:
            if not Agreement.objects.filter(name=name).exists():
                raise CommandError(
                    f"Accord manquant : '{name}'. "
                    "Chargez d'abord : python manage.py loaddata agreements"
                )
        self.stdout.write("  Prérequis ✓")

    # ────────────────────────────────────────────────────────────────────────
    # Helpers de chargement
    # ────────────────────────────────────────────────────────────────────────

    def _load_departments(self):
        from app.reference.models import Department

        depts = {
            d.code: d for d in Department.objects.filter(code__in=("SN", "3EA", "MF2E"))
        }
        self.stdout.write(
            "  Départements : " + ", ".join(f"{c}(pk={d.pk})" for c, d in depts.items())
        )
        return depts

    def _load_level(self, code):
        from app.reference.models import Level

        lvl = Level.objects.get(code=code)
        self.stdout.write(f"  Niveau {code} : pk={lvl.pk}")
        return lvl

    def _load_parcours(self):
        from app.reference.models import Parcours

        dept_to_parcours: dict[str, list] = {}
        for p in Parcours.objects.select_related("department").all():
            dept_to_parcours.setdefault(p.department.code, []).append(p)
        self.stdout.write(
            "  Parcours : "
            + ", ".join(f"{c}={len(ps)}" for c, ps in dept_to_parcours.items())
        )
        return dept_to_parcours

    def _load_countries(self):
        from app.reference.models import Country

        needed = {
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
        }
        cmap = {c.iso2: c for c in Country.objects.filter(iso2__in=needed)}
        if "FR" not in cmap:
            raise CommandError("Pays France (FR) introuvable.")
        missing = needed - set(cmap)
        if missing:
            self.stdout.write(
                self.style.WARNING(f"  Pays introuvables (sera None) : {missing}")
            )
        self.stdout.write(f"  Pays chargés : {', '.join(sorted(cmap))}")
        return cmap

    def _load_current_year(self):
        from app.academic.models import AcademicYear

        year = AcademicYear.objects.get(label="2025-2026")
        self.stdout.write(f"  Année 2025-2026 (pk={year.pk}, statut={year.status})")
        return year

    # ────────────────────────────────────────────────────────────────────────
    # Création des 5 nouveaux accords
    # ────────────────────────────────────────────────────────────────────────

    def _ensure_new_agreements(self, dept_map, country_map, current_year):
        from app.institutions.models import PartnerUniversity
        from app.mobility.models import (
            Agreement,
            AgreementDepartment,
            AgreementYear,
            AgreementYearDepartment,
            MobilityCategory,
        )

        for (
            agr_name,
            univ_name,
            country_iso2,
            cat_name,
            dept_quotas,
            n7_places,
        ) in NEW_AGREEMENTS_DATA:
            category, _ = MobilityCategory.objects.get_or_create(name=cat_name)

            if Agreement.objects.filter(name=agr_name).exists():
                agr = Agreement.objects.get(name=agr_name)
                if agr.category_id is None:
                    Agreement.objects.filter(pk=agr.pk).update(category=category)
                    self.stdout.write(f"  Catégorie ajoutée : {agr_name} → {cat_name}")
                else:
                    self.stdout.write(f"  Accord déjà présent : {agr_name}")
                continue

            country = country_map.get(country_iso2)
            univ, _ = PartnerUniversity.objects.get_or_create(
                name=univ_name,
                defaults={"country": country, "short_name": univ_name[:50]},
            )
            agr = Agreement.objects.create(
                name=agr_name,
                partner_university=univ,
                category=category,
                direction="outgoing",
                inp_total_places=n7_places * 3,
            )
            ay = AgreementYear.objects.create(
                agreement=agr,
                academic_year=current_year,
                is_active=True,
                n7_places=n7_places,
            )
            for dept_code, places in dept_quotas.items():
                dept = dept_map[dept_code]
                ad, _ = AgreementDepartment.objects.get_or_create(
                    agreement=agr, department=dept
                )
                AgreementYearDepartment.objects.get_or_create(
                    agreement_year=ay,
                    agreement_department=ad,
                    defaults={"estimated_places": places},
                )
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Accord créé : {agr_name} ({univ_name})")
            )

    # ────────────────────────────────────────────────────────────────────────
    # Quotas pour les accords existants
    # ────────────────────────────────────────────────────────────────────────

    def _ensure_agreement_year_departments(self, dept_map, current_year):
        from app.mobility.models import (
            Agreement,
            AgreementDepartment,
            AgreementYear,
            AgreementYearDepartment,
        )

        created_count = 0
        for agr_name, dept_quotas, n7_places in ALL_AGREEMENT_QUOTAS_2526:
            agr = Agreement.objects.get(name=agr_name)

            ay, ay_created = AgreementYear.objects.get_or_create(
                agreement=agr,
                academic_year=current_year,
                defaults={"is_active": True, "n7_places": n7_places},
            )
            if not ay_created and ay.n7_places != n7_places:
                AgreementYear.objects.filter(pk=ay.pk).update(n7_places=n7_places)
                self.stdout.write(f"  n7_places mis à jour : {agr_name} → {n7_places}")

            for dept_code, places in dept_quotas.items():
                dept = dept_map[dept_code]
                ad, _ = AgreementDepartment.objects.get_or_create(
                    agreement=agr,
                    department=dept,
                )
                ayd, created = AgreementYearDepartment.objects.get_or_create(
                    agreement_year=ay,
                    agreement_department=ad,
                    defaults={"estimated_places": places},
                )
                if not created and ayd.estimated_places != places:
                    AgreementYearDepartment.objects.filter(pk=ayd.pk).update(
                        estimated_places=places
                    )
                    created_count += 1
                elif created:
                    created_count += 1

        if created_count:
            self.stdout.write(f"  Quotas créés/mis à jour : {created_count}")
        else:
            self.stdout.write("  Quotas : déjà à jour")

    # ────────────────────────────────────────────────────────────────────────
    # Étudiants + inscriptions 2025-2026
    # ────────────────────────────────────────────────────────────────────────

    def _create_students_and_enrollments(
        self, dept_map, level_2ing, level_3ing, country_map, current_year, parcours_map
    ):
        from app.students.models import AnnualEnrollment, Student

        enrollments = []
        batches = [
            (FISE_STUDENTS, level_2ing, False, "FISE 2ING"),
            (FISA_STUDENTS, level_3ing, True, "FISA 3ING"),
        ]

        for students_data, level, is_alternant, label in batches:
            count_new = 0
            for first, last, ine, email, gender, iso2, dept_code, gpa in students_data:
                student, s_created = Student.objects.get_or_create(
                    ine=ine,
                    defaults={
                        "first_name": first,
                        "last_name": last,
                        "email": email,
                        "gender": gender,
                        "nationality": country_map.get(iso2),
                    },
                )
                dept = dept_map[dept_code]
                parcours_list = parcours_map.get(dept_code, [])
                parcours = random.choice(parcours_list) if parcours_list else None
                enrollment, e_created = AnnualEnrollment.objects.get_or_create(
                    student=student,
                    academic_year=current_year,
                    defaults={
                        "department": dept,
                        "level": level,
                        "gpa": gpa,
                        "is_alternant": is_alternant,
                        "parcours": parcours,
                        "is_scholarship": ine in SCHOLARSHIP_INES,
                    },
                )
                if s_created or e_created:
                    count_new += 1
                enrollments.append(enrollment)

            self.stdout.write(
                f"  {label} : {len(students_data)} étudiants ({count_new} nouveaux)"
            )

        return enrollments

    # ────────────────────────────────────────────────────────────────────────
    # Vœux — contrôlés pour garantir tous les scénarios
    # ────────────────────────────────────────────────────────────────────────

    def _create_wishes(self, enrollments, current_year):
        from app.mobility.models import AgreementYear
        from app.students.models import StudentWish

        # Index nom d'accord → AgreementYear pour 2025-2026
        ays_by_name = {
            ay.agreement.name: ay
            for ay in AgreementYear.objects.filter(
                academic_year=current_year, is_active=True
            ).select_related("agreement")
        }

        # Index dept_code → [AgreementYear] avec quota > 0
        dept_to_ays: dict[str, list] = {}
        for ay in AgreementYear.objects.filter(
            academic_year=current_year, is_active=True
        ).prefetch_related("department_quotas__agreement_department__department"):
            for dq in ay.department_quotas.all():
                code = dq.agreement_department.department.code
                if dq.estimated_places > 0:
                    dept_to_ays.setdefault(code, []).append(ay)

        created = 0
        skipped = 0
        for enrollment in enrollments:
            if enrollment.wishes.exists():
                skipped += 1
                continue

            ine = enrollment.student.ine
            dept_code = enrollment.department.code

            if ine in FORCED_WISHES:
                # Vœux imposés : accords sans quota MF2E → slot alternative attendu
                chosen = [
                    ays_by_name[name]
                    for name in FORCED_WISHES[ine]
                    if name in ays_by_name
                ]
            else:
                eligible = dept_to_ays.get(dept_code, [])
                if not eligible:
                    self.stdout.write(
                        self.style.WARNING(f"  Aucun accord pour {dept_code} ({ine})")
                    )
                    continue
                n = min(len(eligible), 3)
                chosen = random.sample(eligible, n)

            for rank, ay in enumerate(chosen, start=1):
                StudentWish.objects.create(
                    annual_enrollment=enrollment,
                    agreement_year=ay,
                    rank=rank,
                )
                created += 1

        self.stdout.write(
            f"  Vœux : {created} créés ({skipped} étudiants déjà pourvus)"
        )
        forced = sum(1 for e in enrollments if e.student.ine in FORCED_WISHES)
        self.stdout.write(
            f"  ⚑  {forced} étudiant(s) MF2E avec vœux forcés "
            "(sans quota MF2E → slot alternative attendu après algo)"
        )

    # ────────────────────────────────────────────────────────────────────────
    # Affectations historiques 2022-2025
    # ────────────────────────────────────────────────────────────────────────

    def _create_historical_assignments(
        self, dept_map, level_2ing, level_3ing, country_map, parcours_map
    ):
        from app.academic.models import AcademicYear
        from app.mobility.models import AgreementYear
        from app.outgoing.models import (
            Assignment,
            AssignmentResult,
            AssignmentStatus,
            SlotType,
        )
        from app.students.models import AnnualEnrollment, Student, StudentWish

        for label in ("2022-2023", "2023-2024", "2024-2025"):
            try:
                year = AcademicYear.objects.get(label=label)
            except AcademicYear.DoesNotExist:
                self.stdout.write(f"  Année {label} absente — ignoré")
                continue

            if Assignment.objects.filter(
                academic_year=year, run_by="seed_dev_data"
            ).exists():
                self.stdout.write(f"  Affectation {label} : déjà présente")
                continue

            agreement_years = list(
                AgreementYear.objects.filter(academic_year=year).prefetch_related(
                    "department_quotas__agreement_department__department"
                )
            )
            if not agreement_years:
                self.stdout.write(f"  Aucun AgreementYear pour {label} — ignoré")
                continue

            dept_to_ays: dict[str, list] = {}
            for ay in agreement_years:
                for dq in ay.department_quotas.all():
                    code = dq.agreement_department.department.code
                    dept_to_ays.setdefault(code, []).append(ay)

            assignment = Assignment.objects.create(
                academic_year=year,
                run_by="seed_dev_data",
                total_students=0,
                assigned_count=0,
                unassigned_count=0,
            )
            Assignment.objects.filter(pk=assignment.pk).update(
                status=AssignmentStatus.PUBLISHED
            )

            results = []
            assigned = unassigned_c = total = 0
            sample = FISE_STUDENTS[:12] + FISE_STUDENTS[14:20] + FISE_STUDENTS[26:30]

            for first, last, ine, email, gender, iso2, dept_code, gpa in sample:
                student, _ = Student.objects.get_or_create(
                    ine=ine,
                    defaults={
                        "first_name": first,
                        "last_name": last,
                        "email": email,
                        "gender": gender,
                        "nationality": country_map.get(iso2),
                    },
                )
                dept = dept_map.get(dept_code)
                if not dept:
                    continue

                parcours_list = parcours_map.get(dept_code, [])
                parcours = random.choice(parcours_list) if parcours_list else None

                enrollment, _ = AnnualEnrollment.objects.get_or_create(
                    student=student,
                    academic_year=year,
                    defaults={
                        "department": dept,
                        "level": level_2ing,
                        "gpa": gpa,
                        "is_alternant": False,
                        "parcours": parcours,
                        "is_scholarship": ine in SCHOLARSHIP_INES,
                    },
                )
                total += 1

                eligible = dept_to_ays.get(dept_code, [])

                # Vœux : créés avant l'affectation (cohérence stats)
                wish_ays: list = []
                if eligible and not enrollment.wishes.exists():
                    n_wish = min(len(eligible), random.randint(2, 3))
                    wish_ays = random.sample(eligible, n_wish)
                    for rank, ay in enumerate(wish_ays, start=1):
                        StudentWish.objects.create(
                            annual_enrollment=enrollment,
                            agreement_year=ay,
                            rank=rank,
                        )

                # Affectation : 85 % des étudiants avec vœux → affecté au vœu 1
                if wish_ays and random.random() > 0.15:
                    results.append(
                        AssignmentResult(
                            assignment=assignment,
                            annual_enrollment=enrollment,
                            agreement_year=wish_ays[0],
                            slot_type=random.choice([SlotType.DEPT, SlotType.SURPLUS]),
                            assigned_rank=1,
                        )
                    )
                    assigned += 1
                else:
                    results.append(
                        AssignmentResult(
                            assignment=assignment,
                            annual_enrollment=enrollment,
                            agreement_year=None,
                            slot_type=SlotType.UNASSIGNED,
                        )
                    )
                    unassigned_c += 1

            AssignmentResult.objects.bulk_create(results, ignore_conflicts=True)
            Assignment.objects.filter(pk=assignment.pk).update(
                total_students=total,
                assigned_count=assigned,
                unassigned_count=unassigned_c,
            )
            self.stdout.write(
                f"  Affectation {label} : {assigned}/{total} affectés (publiée)"
            )
