import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0002_academicyear_closed_at"),
        ("imports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RawImport",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.CharField(max_length=255)),
                ("source_file", models.CharField(blank=True, max_length=255)),
                ("external_id", models.CharField(max_length=255)),
                ("payload", models.JSONField()),
                (
                    "entity",
                    models.CharField(
                        choices=[
                            ("department", "Département"),
                            ("level", "Niveau"),
                            ("partner_university", "Université partenaire"),
                            ("agreement_category", "Catégorie d'accord"),
                            ("agreement", "Accord"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("imported", "Importé"),
                            ("failed", "Échoué"),
                            ("ignored", "Ignoré"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("imported_at", models.DateTimeField(blank=True, null=True)),
                (
                    "academic_year",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="raw_imports",
                        to="academic.academicyear",
                        verbose_name="Année universitaire",
                    ),
                ),
                (
                    "import_report",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="raw_imports",
                        to="imports.importreport",
                        verbose_name="Rapport d'import",
                    ),
                ),
            ],
            options={
                "verbose_name": "Import brut",
                "verbose_name_plural": "Imports bruts",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="rawimport",
            index=models.Index(
                fields=["entity", "external_id"], name="imports_raw_entity_extid_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="rawimport",
            index=models.Index(fields=["status"], name="imports_raw_status_idx"),
        ),
        migrations.AddIndex(
            model_name="rawimport",
            index=models.Index(fields=["entity"], name="imports_raw_entity_idx"),
        ),
        migrations.AddIndex(
            model_name="rawimport",
            index=models.Index(fields=["import_report"], name="imports_raw_report_idx"),
        ),
    ]
