from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from app.mobility.models import AgreementYear


class Command(BaseCommand):
    help = (
        "Remplit la colonne duration_weeks des instances annuelles d'accord. "
        "Sans --apply : dry-run uniquement."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--default",
            type=int,
            default=20,
            metavar="SEMAINES",
            help="Durée en semaines à appliquer aux instances sans durée (défaut : 20).",
        )
        parser.add_argument(
            "--year",
            metavar="LABEL",
            help="Restreindre à une seule année universitaire (ex: 2024-2025).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Écraser aussi les instances qui ont déjà une durée renseignée.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Appliquer les modifications. Sans ce flag : dry-run uniquement.",
        )

    def handle(self, *args, **options):
        default_weeks = options["default"]
        year_label = options["year"]
        force = options["force"]
        apply = options["apply"]

        if default_weeks <= 0:
            raise CommandError("--default doit être un entier positif.")

        qs = AgreementYear.objects.select_related("agreement", "academic_year")
        if year_label:
            qs = qs.filter(academic_year__label=year_label)
        if not force:
            qs = qs.filter(duration_weeks__isnull=True)

        instances = list(qs.order_by("academic_year__label", "agreement__name"))

        if not instances:
            self.stdout.write(self.style.SUCCESS("Aucune instance à mettre à jour."))
            return

        prefix = "" if apply else "[DRY-RUN] "
        self.stdout.write(
            self.style.WARNING(
                f"{prefix}{len(instances)} instance(s) seront mises à jour "
                f"(duration_weeks → {default_weeks} sem.) :"
            )
        )
        for yi in instances:
            current = (
                f"{yi.duration_weeks} sem." if yi.duration_weeks is not None else "—"
            )
            self.stdout.write(
                f"  • [{yi.id}] {yi.agreement.name} | {yi.academic_year.label} "
                f"(actuel : {current} → {default_weeks} sem.)"
            )

        if not apply:
            self.stdout.write(
                self.style.NOTICE(
                    "\nAucune modification effectuée. "
                    "Relancez avec --apply pour appliquer les changements."
                )
            )
            return

        with transaction.atomic():
            updated = qs.update(duration_weeks=default_weeks)

        self.stdout.write(
            self.style.SUCCESS(
                f"{updated} instance(s) mises à jour avec {default_weeks} sem."
            )
        )
