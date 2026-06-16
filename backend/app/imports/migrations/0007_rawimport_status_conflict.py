from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0006_add_academic_year_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rawimport",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "En attente"),
                    ("imported", "Importé"),
                    ("failed", "Échoué"),
                    ("ignored", "Ignoré"),
                    ("conflict", "Conflit"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
