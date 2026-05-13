from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reference", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="pegase_id",
            field=models.CharField(
                max_length=50,
                unique=True,
                null=True,
                blank=True,
                verbose_name="Identifiant Pegase",
            ),
        ),
        migrations.AddField(
            model_name="department",
            name="last_sync_pegase",
            field=models.DateTimeField(
                null=True,
                blank=True,
                verbose_name="Date dernier sync Pegase",
            ),
        ),
        migrations.CreateModel(
            name="DepartmentRawImport",
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
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "source",
                    models.CharField(max_length=255),
                ),
                (
                    "source_file",
                    models.CharField(max_length=255, blank=True),
                ),
                (
                    "external_id",
                    models.CharField(max_length=255),
                ),
                (
                    "payload",
                    models.JSONField(),
                ),
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
                (
                    "error_message",
                    models.TextField(blank=True),
                ),
                (
                    "imported_at",
                    models.DateTimeField(null=True, blank=True),
                ),
            ],
            options={
                "verbose_name": "Department Raw Import",
                "verbose_name_plural": "Department Raw Imports",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["source", "external_id"],
                        name="reference_departmentrawimport_source_external_id_idx",
                    ),
                    models.Index(
                        fields=["status"],
                        name="reference_departmentrawimport_status_idx",
                    ),
                ],
            },
        ),
    ]
