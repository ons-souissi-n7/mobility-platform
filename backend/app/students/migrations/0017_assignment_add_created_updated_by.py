from django.db import migrations


class Migration(migrations.Migration):
    """
    Champs created_by/updated_by ajoutés directement dans la migration initiale
    de app.outgoing (0001_initial). Conservé pour la chaîne de dépendances.
    """

    dependencies = [
        ("students", "0016_annualenrollment_is_alternant_is_scholarship"),
    ]

    operations = []
