from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0041_agreementyear_inp_total_places"),
    ]

    operations = [
        migrations.AddField(
            model_name="agreementyear",
            name="duration_weeks",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name="Durée (semaines)",
                help_text="Durée standard du séjour en semaines, utilisée pour le calcul CTI.",
            ),
        ),
    ]
