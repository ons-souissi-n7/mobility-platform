from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reference", "0010_parcours_unique_together_to_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="level",
            name="is_terminal",
            field=models.BooleanField(
                default=False,
                help_text="Cocher si c'est le dernier niveau du cursus (ex: 3A ingénieur, M2). Utilisé pour calculer la cohorte CTI.",
                verbose_name="Niveau terminal (diplômant)",
            ),
        ),
    ]
