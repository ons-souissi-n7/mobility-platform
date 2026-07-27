import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("students", "0017_assignment_add_created_updated_by"),
    ]

    operations = [
        migrations.CreateModel(
            name="MobilityDuration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "updated_by",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "student",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cti_duration",
                        to="students.student",
                        verbose_name="Étudiant",
                    ),
                ),
                (
                    "exchange_weeks",
                    models.DecimalField(
                        decimal_places=1,
                        default=0,
                        max_digits=6,
                        verbose_name="Échange universitaire (sem.)",
                    ),
                ),
                (
                    "internship_weeks",
                    models.DecimalField(
                        decimal_places=1,
                        default=0,
                        max_digits=6,
                        verbose_name="Stage international (sem.)",
                    ),
                ),
                (
                    "complementary_weeks",
                    models.DecimalField(
                        decimal_places=1,
                        default=0,
                        max_digits=6,
                        verbose_name="Mobilité complémentaire (sem.)",
                    ),
                ),
                (
                    "total_weeks",
                    models.DecimalField(
                        decimal_places=1,
                        default=0,
                        max_digits=6,
                        verbose_name="Total (sem.)",
                    ),
                ),
                (
                    "meets_cti",
                    models.BooleanField(
                        default=False, verbose_name="Répond au critère CTI"
                    ),
                ),
            ],
            options={
                "verbose_name": "Durée CTI",
                "verbose_name_plural": "Durées CTI",
                "ordering": ["-total_weeks"],
            },
        ),
    ]
