from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0006_student_nationality"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="pegase_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Identifiant Pégase",
            ),
        ),
        migrations.AddField(
            model_name="student",
            name="last_sync_pegase",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Dernière sync Pégase",
            ),
        ),
    ]
