"""
Attache un justificatif PDF de démonstration à chaque ComplementaryMobility
qui n'en a pas encore, en passant par le vrai chemin d'upload MinIO
(`upload_document`) — pour que la colonne "Justificatif" et la fenêtre de
détail de l'admin (icône œil) aient réellement quelque chose à afficher.

Additif et idempotent : ne touche jamais un enregistrement qui a déjà un
`document_key` (ne remplace pas un vrai justificatif déposé par un
étudiant), ne modifie aucune autre donnée.

Le PDF est construit à la main (pas de dépendance externe type reportlab) :
un squelette PDF minimal mais valide, avec une table xref aux bons offsets,
un flux de texte reprenant les infos de la déclaration pour que chaque
fichier soit visuellement distinct plutôt qu'un simple gabarit vide.
"""

import unicodedata

from django.core.management.base import BaseCommand


def _ascii(text: str) -> str:
    """Translittère en ASCII simple — évite les soucis d'encodage PDF avec
    les accents dans la police de base (Helvetica, sans /Encoding déclaré)."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _build_minimal_pdf(lines: list[str]) -> bytes:
    """Construit un PDF à une page listant `lines`, avec des offsets xref
    calculés (pas de table à zéro) pour rester compatible avec les lecteurs
    stricts, pas seulement le mode de récupération des navigateurs."""
    stream_parts = ["BT", "/F1 13 Tf", "20 180 Td"]
    for i, line in enumerate(lines):
        if i > 0:
            stream_parts.append("0 -18 Td")
        stream_parts.append(f"({_pdf_escape(_ascii(line))}) Tj")
    stream_parts.append("ET")
    stream_content = "\n".join(stream_parts).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 220] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        (b"<< /Length %d >>\nstream\n" % len(stream_content))
        + stream_content
        + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    buf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(buf))
        buf += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_offset = len(buf)
    buf += f"xref\n0 {len(objects) + 1}\n".encode()
    buf += b"0000000000 65535 f \n"
    for off in offsets:
        buf += f"{off:010d} 00000 n \n".encode()
    buf += b"trailer\n"
    buf += f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode()
    buf += b"startxref\n"
    buf += f"{xref_offset}\n".encode()
    buf += b"%%EOF"
    return bytes(buf)


class Command(BaseCommand):
    help = (
        "Attache un justificatif PDF de démonstration (upload MinIO réel) à "
        "chaque mobilité complémentaire qui n'en a pas encore. Additif, "
        "idempotent, ne touche jamais un justificatif déjà déposé."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--year-label",
            default=None,
            help="Limiter à une année universitaire (défaut : toutes).",
        )

    def handle(self, *args, **options):
        from app.complementary.models import ComplementaryMobility
        from app.complementary.services.minio_service import upload_document

        qs = ComplementaryMobility.objects.filter(document_key="").select_related(
            "student", "academic_year", "destination_country"
        )
        if options["year_label"]:
            qs = qs.filter(academic_year__label=options["year_label"])

        total = qs.count()
        if total == 0:
            self.stdout.write(
                "Aucune mobilité complémentaire sans justificatif à traiter."
            )
            return

        updated = 0
        for mob in qs.iterator():
            student_name = f"{mob.student.first_name} {mob.student.last_name}"
            destination = mob.destination_institution or mob.destination_country.name_fr
            lines = [
                "JUSTIFICATIF DE MOBILITE COMPLEMENTAIRE (document de demonstration)",
                "",
                f"Etudiant : {student_name} ({mob.student.ine})",
                f"Annee universitaire : {mob.academic_year.label}",
                f"Type d'experience : {mob.experience_type}",
                f"Destination : {destination} ({mob.destination_country.name_fr})",
                f"Periode : {mob.start_date} au {mob.end_date}",
                "",
                "Ce fichier est genere automatiquement a des fins de demonstration",
                "et ne constitue pas un justificatif reel.",
            ]
            pdf_bytes = _build_minimal_pdf(lines)
            doc_name = f"justificatif_{mob.student.ine}_{mob.id}.pdf"
            key = upload_document(pdf_bytes, doc_name, "application/pdf")

            mob.document_key = key
            mob.document_name = doc_name
            mob.save(update_fields=["document_key", "document_name", "updated_at"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ {updated} justificatif(s) PDF uploadé(s) sur MinIO et rattaché(s)."
            )
        )
