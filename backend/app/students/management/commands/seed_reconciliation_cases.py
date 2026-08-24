"""
Seed de cas de réconciliation (RawImport en échec faute d'INE valide), pour
tester l'écran "Réconciliation — étudiant similaire" (WishImportErrorsPanel,
admin > Mobilité sortante > erreurs d'import de vœux).

Reproduit exactement la forme produite par le pipeline réel
(sync_moveon.import_wish_rows / _mark_wish_unresolved) pour qu'un vrai
GET /api/v1/outgoing/wishes/import-errors/ les retrouve : entity=STUDENT,
source="moveon_student_wishes", status=FAILED, error_message contenant
"Étudiant introuvable".

Additif : ne modifie ni ne supprime aucune donnée existante (ni Student, ni
RawImport). Rejouable — les external_id sont préfixés "QA-RECON-" et
vérifiés avant création.

`random` sert uniquement à générer des cas de démonstration plausibles.
Sans objet pour les hotspots Sonar "pseudorandom number generator" (S2245).
"""

import random

from django.core.management.base import BaseCommand
from django.db import transaction

# Noms entièrement fictifs, choisis pour ne matcher aucun étudiant réel —
# couvre le cas "aucun candidat trouvé" de l'écran de réconciliation.
FICTIONAL_NAMES = [
    ("Zoltan", "KRAVETZ"),
    ("Ingeborg", "VANDENBROECKE"),
    ("Yusra", "AL-MANSOURI"),
]


def _typo(name: str) -> str:
    """Permute deux caractères adjacents pour simuler une faute de frappe."""
    if len(name) < 4:
        return name
    i = random.randint(1, len(name) - 2)  # NOSONAR (S2245) — donnée de démo
    chars = list(name)
    chars[i], chars[i + 1] = chars[i + 1], chars[i]
    return "".join(chars)


class Command(BaseCommand):
    help = (
        "Seed des cas de réconciliation (vœux MoveOn importés sans INE "
        "valide) pour tester l'écran de réconciliation admin. Additif, "
        "rejouable, ne touche à aucune donnée existante."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--year-label",
            default=None,
            help="Année universitaire cible (défaut : la plus récente en base).",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=8,
            help="Nombre de cas à générer (défaut : 8, couvre les 4 profils "
            "de confiance : haute/moyenne/moyenne-faible/aucune).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=7,
            help="Graine aléatoire pour la reproductibilité (défaut: 7).",
        )

    def handle(self, *args, **options):
        from app.academic.models import AcademicYear
        from app.imports.models import RawImport, RawImportEntity, RawImportStatus
        from app.mobility.models import Agreement
        from app.students.models import Student

        random.seed(options["seed"])  # NOSONAR (S2245) — donnée de démo

        year = (
            AcademicYear.objects.filter(label=options["year_label"]).first()
            if options["year_label"]
            else AcademicYear.objects.order_by("-start_date").first()
        )
        if year is None:
            self.stderr.write(self.style.ERROR("Aucune année universitaire en base."))
            return

        real_students = list(Student.objects.order_by("?")[:20])
        if len(real_students) < 3:
            self.stderr.write(
                self.style.ERROR(
                    "Pas assez d'étudiants en base pour générer des cas réalistes."
                )
            )
            return

        agreement_names = list(
            Agreement.objects.order_by("?").values_list("name", flat=True)[:20]
        )

        created = 0
        count = options["count"]
        with transaction.atomic():
            for i in range(count):
                rank = 1 + (i % 3)
                offre = (
                    random.choice(agreement_names)  # NOSONAR (S2245)
                    if agreement_names
                    else "Erasmus+"
                )

                tier = i % 4
                email = ""
                if tier == 0 and real_students:
                    # Confiance haute : nom identique à un étudiant existant
                    # ET email connu — cas où MoveOn fournit l'email mais pas
                    # l'INE (rattachement Pégase pas encore fait).
                    student = real_students.pop()
                    first, last = student.first_name, student.last_name.upper()
                    email = student.email
                elif tier == 1 and real_students:
                    # Confiance moyenne : nom identique, mais pas d'email
                    # fourni — l'algorithme plafonne alors à "medium" (le
                    # score email ne peut jamais contribuer sans indice).
                    student = real_students.pop()
                    first, last = student.first_name, student.last_name.upper()
                elif tier == 2 and real_students:
                    # Confiance moyenne/faible : une faute de frappe sur le nom.
                    student = real_students.pop()
                    first, last = student.first_name, _typo(student.last_name.upper())
                else:
                    # Aucune correspondance possible : nom entièrement fictif.
                    first, last = random.choice(FICTIONAL_NAMES)  # NOSONAR (S2245)

                individu = f"{last} {first}"
                external_id = f"QA-RECON-{year.label}-rank{rank}-{i:03d}"
                if RawImport.objects.filter(external_id=external_id).exists():
                    continue

                RawImport.objects.create(
                    source="moveon_student_wishes",
                    source_file="",
                    entity=RawImportEntity.STUDENT,
                    external_id=external_id,
                    payload={
                        "ine": "",
                        "individu": individu,
                        "email": email,
                        "offre_de_sejour": offre,
                        "moveon_offer_id": f"MO-{1000 + i}",
                        "rank": rank,
                    },
                    status=RawImportStatus.FAILED,
                    error_message=(
                        f"Étudiant introuvable (INE : '', Individu : {individu!r})"
                    ),
                    academic_year=year,
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ {created} cas de réconciliation créés pour {year.label} "
                f"(entity=student, source=moveon_student_wishes, status=failed)."
            )
        )
        self.stdout.write(
            "  → Consultables dans l'admin, Mobilité sortante > erreurs "
            "d'import de vœux, ou via GET /api/v1/outgoing/wishes/import-errors/"
        )
