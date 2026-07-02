from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("outgoing", "0003_add_override_slot_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignmentresult",
            name="override_rank",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name="Rang du vœu retenu (correction manuelle)",
            ),
        ),
    ]
