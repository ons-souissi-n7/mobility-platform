from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("academic", "0001_initial"),
        ("institutions", "0001_initial"),
        ("mobility", "0001_initial"),
        ("reference", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="IncomingStudent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="incoming_students",
                        to="academic.academicyear",
                        verbose_name="Année universitaire",
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incoming_students",
                        to="reference.department",
                        verbose_name="Département N7",
                    ),
                ),
                (
                    "civility",
                    models.CharField(
                        blank=True, max_length=10, verbose_name="Civilité"
                    ),
                ),
                ("last_name", models.CharField(max_length=255, verbose_name="Nom")),
                ("first_name", models.CharField(max_length=255, verbose_name="Prénom")),
                (
                    "country",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incoming_students",
                        to="reference.country",
                        verbose_name="Pays",
                    ),
                ),
                (
                    "origin_university",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incoming_students",
                        to="institutions.partneruniversity",
                        verbose_name="Université d'origine (liée)",
                    ),
                ),
                (
                    "origin_university_name",
                    models.CharField(
                        blank=True, max_length=500, verbose_name="Université d'origine"
                    ),
                ),
                (
                    "birth_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Date de naissance"
                    ),
                ),
                (
                    "mobility_category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incoming_students",
                        to="mobility.mobilitycategory",
                        verbose_name="Cadre de mobilité",
                    ),
                ),
                (
                    "personal_email",
                    models.EmailField(blank=True, verbose_name="Email personnel"),
                ),
                (
                    "n7_email",
                    models.EmailField(blank=True, verbose_name="Email ENSEEIHT"),
                ),
                (
                    "duration",
                    models.CharField(blank=True, max_length=100, verbose_name="Durée"),
                ),
                (
                    "level",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incoming_students",
                        to="reference.level",
                        verbose_name="Niveau / Année",
                    ),
                ),
                (
                    "parcours",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incoming_students",
                        to="reference.parcours",
                        verbose_name="Parcours",
                    ),
                ),
                ("remarks", models.TextField(blank=True, verbose_name="Remarques")),
                ("internship_info", models.TextField(blank=True, verbose_name="Stage")),
                ("diploma_info", models.TextField(blank=True, verbose_name="Diplôme")),
                (
                    "doctoral_continuation",
                    models.BooleanField(
                        default=False, verbose_name="Poursuite doctorat"
                    ),
                ),
            ],
            options={
                "verbose_name": "Étudiant entrant",
                "verbose_name_plural": "Étudiants entrants",
                "ordering": ["-academic_year__start_date", "last_name", "first_name"],
            },
        ),
        migrations.AddConstraint(
            model_name="incomingstudent",
            constraint=models.UniqueConstraint(
                fields=["academic_year", "last_name", "first_name", "birth_date"],
                name="unique_incoming_year_name_birthdate",
            ),
        ),
        migrations.AddIndex(
            model_name="incomingstudent",
            index=models.Index(fields=["academic_year"], name="incoming_year_idx"),
        ),
        migrations.AddIndex(
            model_name="incomingstudent",
            index=models.Index(fields=["country"], name="incoming_country_idx"),
        ),
        migrations.AddIndex(
            model_name="incomingstudent",
            index=models.Index(fields=["department"], name="incoming_dept_idx"),
        ),
        migrations.AddIndex(
            model_name="incomingstudent",
            index=models.Index(
                fields=["last_name", "first_name"], name="incoming_name_idx"
            ),
        ),
    ]
