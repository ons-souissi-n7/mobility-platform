from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0015_add_assignment_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="annualenrollment",
            name="is_alternant",
            field=models.BooleanField(
                default=False,
                help_text="Vrai pour les étudiants en apprentissage (FISA). "
                "Les FISA choisissent leur mobilité en 3ème année.",
                verbose_name="Alternant (FISA)",
            ),
        ),
        migrations.AddField(
            model_name="annualenrollment",
            name="is_scholarship",
            field=models.BooleanField(
                default=False,
                verbose_name="Boursier",
            ),
        ),
        migrations.AddIndex(
            model_name="annualenrollment",
            index=models.Index(
                fields=["academic_year", "is_alternant"],
                name="enroll_year_alternant_idx",
            ),
        ),
    ]
