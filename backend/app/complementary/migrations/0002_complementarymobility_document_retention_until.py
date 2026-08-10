from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("complementary", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="complementarymobility",
            name="document_retention_until",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="Conserver le justificatif jusqu'au",
                help_text="Date d'expiration du délai de conservation RGPD ; après cette date le fichier est supprimé automatiquement.",
            ),
        ),
    ]
