from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SystemAlert",
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
                (
                    "created_by",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "updated_by",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "level",
                    models.CharField(
                        choices=[("warning", "Avertissement"), ("error", "Erreur")],
                        default="warning",
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Alerte système",
                "verbose_name_plural": "Alertes système",
                "ordering": ["-created_at"],
            },
        ),
    ]
