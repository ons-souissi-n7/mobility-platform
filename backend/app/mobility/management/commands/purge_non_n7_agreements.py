from django.core.management.base import BaseCommand
from django.db import transaction

from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.mobility.models import Agreement
from app.mobility.services.sync_moveon import _n7_is_present


class Command(BaseCommand):
    help = (
        "Supprime (ou liste) les accords MoveOn où N7/ENSEEIHT est absent "
        "du champ Etablissements internes. Ces accords ne concernent pas N7."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Supprime réellement les accords sans N7. Sans ce flag : dry-run uniquement.",
        )

    def handle(self, *args, **options):
        do_delete = options["delete"]

        non_n7 = [
            a
            for a in Agreement.objects.select_related("partner_university").all()
            if not _n7_is_present(a.inp_institutions)
        ]

        if not non_n7:
            self.stdout.write(self.style.SUCCESS("Aucun accord sans N7 trouvé."))
            return

        self.stdout.write(
            self.style.WARNING(
                f"{'[DRY-RUN] ' if not do_delete else ''}"
                f"{len(non_n7)} accord(s) sans N7/ENSEEIHT :"
            )
        )
        for a in non_n7:
            uni = a.partner_university.name if a.partner_university else "?"
            self.stdout.write(
                f"  • [{a.pk}] {a.name} — {uni}"
                f" (inp_institutions={repr(a.inp_institutions) or 'vide'})"
            )

        if not do_delete:
            self.stdout.write(
                self.style.NOTICE(
                    "\nAucune modification effectuée. "
                    "Relancez avec --delete pour supprimer ces accords."
                )
            )
            return

        with transaction.atomic():
            deleted_count = 0
            for a in non_n7:
                moveon_id = a.moveon_id
                a.delete()
                deleted_count += 1
                if moveon_id:
                    RawImport.objects.filter(
                        external_id=moveon_id,
                        entity=RawImportEntity.AGREEMENT,
                    ).update(
                        status=RawImportStatus.IGNORED,
                        error_message="N7/ENSEEIHT absent des établissements INP de cet accord",
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"{deleted_count} accord(s) supprimé(s) et RawImports marqués IGNORED."
            )
        )
