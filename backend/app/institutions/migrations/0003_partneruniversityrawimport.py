from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "institutions",
            "0002_rename_institutio_moveon__6ba91b_idx_institution_moveon__3f8703_idx_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="PartnerUniversityRawImport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source", models.CharField(max_length=255)),
                ("source_file", models.CharField(blank=True, max_length=255)),
                ("external_id", models.CharField(max_length=255)),
                ("payload", models.JSONField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("imported", "Imported"),
                            ("failed", "Failed"),
                            ("ignored", "Ignored"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("imported_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Partner University Raw Import",
                "verbose_name_plural": "Partner University Raw Imports",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="partneruniversityrawimport",
            index=models.Index(
                fields=["source", "external_id"],
                name="institution_source_f55e99_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="partneruniversityrawimport",
            index=models.Index(fields=["status"], name="institution_status_8db0e8_idx"),
        ),
    ]
