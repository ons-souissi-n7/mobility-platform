from django.db import migrations


class Migration(migrations.Migration):
    """
    Modèles Assignment et AssignmentResult déplacés dans app.outgoing.
    Cette migration est conservée pour maintenir la chaîne de dépendances.
    """

    dependencies = [
        ("mobility", "0038_nomenclaturemapping"),
        ("academic", "0001_initial"),
        ("students", "0014_studentwish_agreement_to_agreement_year"),
    ]

    operations = []
