import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("academic", "0002_academicyear_closed_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImportReport",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("moveon_accords", "MoveON – Accords"),
                            ("moveon_categories", "MoveON – Catégories"),
                            ("moveon_quotas", "MoveON – Quotas"),
                            ("pegase", "Pégase – Étudiants"),
                            ("eudonet", "Eudonet – Stages"),
                            ("excel", "Import Excel"),
                        ],
                        max_length=50,
                        verbose_name="Source",
                    ),
                ),
                (
                    "academic_year",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="import_reports",
                        to="academic.academicyear",
                        verbose_name="Année universitaire",
                    ),
                ),
                ("total", models.IntegerField(default=0, verbose_name="Total traités")),
                (
                    "success_count",
                    models.IntegerField(default=0, verbose_name="Succès"),
                ),
                ("error_count", models.IntegerField(default=0, verbose_name="Erreurs")),
                (
                    "duplicate_count",
                    models.IntegerField(default=0, verbose_name="Doublons ignorés"),
                ),
                (
                    "errors",
                    models.JSONField(default=list, verbose_name="Détail des erreurs"),
                ),
                (
                    "triggered_by",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Déclenché par"
                    ),
                ),
            ],
            options={
                "verbose_name": "Rapport d'import",
                "verbose_name_plural": "Rapports d'import",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="importreport",
            index=models.Index(fields=["source"], name="imports_report_source_idx"),
        ),
        migrations.AddIndex(
            model_name="importreport",
            index=models.Index(
                fields=["academic_year"], name="imports_report_year_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="importreport",
            index=models.Index(fields=["-created_at"], name="imports_report_date_idx"),
        ),
    ]
