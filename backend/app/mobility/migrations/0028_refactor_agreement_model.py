"""
Refactor complet du modèle Agreement :
- Suppression : AgreementYearAvailability, AgreementQuota, DepartmentQuota
- Suppression des champs obsolètes sur Agreement
- Renommage start_date→valid_from, end_date→valid_until
- Ajout : inp_total_places, inp_institutions
- Création : AgreementYear, AgreementYearDepartment
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0002_academicyear_closed_at"),
        ("mobility", "0027_alter_agreementquota_options_and_more"),
        ("reference", "0007_alter_country_id_alter_department_id_and_more"),
        ("institutions", "0004_alter_partneruniversity_id_and_more"),
    ]

    operations = [
        # ── 1. Supprimer DepartmentQuota (dépend de AgreementQuota) ──────────
        migrations.DeleteModel(name="DepartmentQuota"),
        # ── 2. Supprimer AgreementQuota ──────────────────────────────────────
        migrations.DeleteModel(name="AgreementQuota"),
        # ── 3. Supprimer AgreementYearAvailability ───────────────────────────
        migrations.DeleteModel(name="AgreementYearAvailability"),
        # ── 4. Supprimer les indexes qui référencent les champs à supprimer ──
        # Index sur (partner_university, is_active) — ajouté en migration 0002
        migrations.RemoveIndex(
            model_name="agreement",
            name="mobility_ag_partner_a6a955_idx",
        ),
        # Index sur status — ajouté en migration 0001
        migrations.RemoveIndex(
            model_name="agreement",
            name="mobility_ag_status_3e1a44_idx",
        ),
        # ── 5. Supprimer les champs obsolètes de Agreement ───────────────────
        migrations.RemoveField(model_name="agreement", name="is_active"),
        migrations.RemoveField(model_name="agreement", name="status"),
        migrations.RemoveField(model_name="agreement", name="relation_type"),
        migrations.RemoveField(model_name="agreement", name="category_name"),
        migrations.RemoveField(model_name="agreement", name="start_academic_year"),
        migrations.RemoveField(model_name="agreement", name="end_academic_year"),
        migrations.RemoveField(model_name="agreement", name="discipline"),
        migrations.RemoveField(model_name="agreement", name="isced"),
        migrations.RemoveField(model_name="agreement", name="level"),
        migrations.RemoveField(model_name="agreement", name="formation"),
        migrations.RemoveField(model_name="agreement", name="url"),
        migrations.RemoveField(model_name="agreement", name="restrictions"),
        # ── 6. Renommer start_date → valid_from, end_date → valid_until ──────
        migrations.RenameField(
            model_name="agreement",
            old_name="start_date",
            new_name="valid_from",
        ),
        migrations.RenameField(
            model_name="agreement",
            old_name="end_date",
            new_name="valid_until",
        ),
        # ── 7. Ajouter nouveaux champs sur Agreement ─────────────────────────
        migrations.AddField(
            model_name="agreement",
            name="inp_total_places",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="agreement",
            name="inp_institutions",
            field=models.CharField(blank=True, max_length=500),
        ),
        # ── 8. Mettre à jour les options de Agreement ────────────────────────
        migrations.AlterModelOptions(
            name="agreement",
            options={
                "ordering": ["name"],
                "verbose_name": "Agreement",
                "verbose_name_plural": "Agreements",
            },
        ),
        # ── 9. Ajouter un index propre sur partner_university seul ───────────
        migrations.AddIndex(
            model_name="agreement",
            index=models.Index(
                fields=["partner_university"],
                name="mobility_agreement_partner_idx",
            ),
        ),
        # ── 10. Créer AgreementYear ───────────────────────────────────────────
        migrations.CreateModel(
            name="AgreementYear",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("n7_places", models.IntegerField(default=0)),
                ("is_validated", models.BooleanField(default=False)),
                ("validated_by", models.CharField(blank=True, max_length=255)),
                ("validated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "agreement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="year_instances",
                        to="mobility.agreement",
                    ),
                ),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="agreement_years",
                        to="academic.academicyear",
                    ),
                ),
            ],
            options={
                "verbose_name": "Agreement Year",
                "verbose_name_plural": "Agreement Years",
                "ordering": ["-academic_year__label", "agreement__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="agreementyear",
            constraint=models.UniqueConstraint(
                fields=("agreement", "academic_year"),
                name="unique_agreement_year",
            ),
        ),
        migrations.AddIndex(
            model_name="agreementyear",
            index=models.Index(
                fields=["agreement", "academic_year"],
                name="mobility_agreementyear_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="agreementyear",
            index=models.Index(
                fields=["is_active"],
                name="mobility_agreementyear_active_idx",
            ),
        ),
        # ── 11. Créer AgreementYearDepartment ────────────────────────────────
        migrations.CreateModel(
            name="AgreementYearDepartment",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("estimated_places", models.IntegerField(default=0)),
                (
                    "agreement_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="department_quotas",
                        to="mobility.agreementyear",
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="agreement_year_departments",
                        to="reference.department",
                    ),
                ),
            ],
            options={
                "verbose_name": "Agreement Year Department",
                "verbose_name_plural": "Agreement Year Departments",
                "ordering": ["department__code"],
            },
        ),
        migrations.AddConstraint(
            model_name="agreementyeardepartment",
            constraint=models.UniqueConstraint(
                fields=("agreement_year", "department"),
                name="unique_agreement_year_department",
            ),
        ),
        migrations.AddIndex(
            model_name="agreementyeardepartment",
            index=models.Index(
                fields=["agreement_year", "department"],
                name="mobility_agrdept_idx",
            ),
        ),
        # ── 12. Mettre à jour RawImportEntity choices ─────────────────────────
        migrations.AlterField(
            model_name="rawimport",
            name="entity",
            field=models.CharField(
                choices=[
                    ("partner_university", "Partner University"),
                    ("agreement_category", "Agreement Category"),
                    ("agreement", "Agreement"),
                ],
                default="partner_university",
                max_length=50,
            ),
        ),
    ]
