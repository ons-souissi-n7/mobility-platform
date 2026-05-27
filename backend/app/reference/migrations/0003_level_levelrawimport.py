from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reference", "0002_pegase_department_imports"),
    ]

    operations = [
        migrations.CreateModel(
            name="Level",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "pegase_id",
                    models.CharField(blank=True, max_length=50, null=True, unique=True),
                ),
                ("last_sync_pegase", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Level",
                "verbose_name_plural": "Levels",
                "ordering": ["code"],
            },
        ),
        migrations.AddIndex(
            model_name="level",
            index=models.Index(fields=["code"], name="reference_l_code_idx"),
        ),
        migrations.AddIndex(
            model_name="level",
            index=models.Index(fields=["is_active"], name="reference_l_is_acti_idx"),
        ),
        migrations.CreateModel(
            name="LevelRawImport",
            fields=[
                (
                    "id",
                    models.AutoField(
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
                "verbose_name": "Level Raw Import",
                "verbose_name_plural": "Level Raw Imports",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="levelrawimport",
            index=models.Index(
                fields=["source", "external_id"], name="reference_l_source_extid_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="levelrawimport",
            index=models.Index(fields=["status"], name="reference_l_status_idx"),
        ),
    ]
