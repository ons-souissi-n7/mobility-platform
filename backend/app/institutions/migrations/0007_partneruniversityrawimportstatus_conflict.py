from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("institutions", "0006_partneruniversity_univ_name_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="partneruniversityrawimport",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("imported", "Imported"),
                    ("failed", "Failed"),
                    ("ignored", "Ignored"),
                    ("conflict", "Conflit"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
