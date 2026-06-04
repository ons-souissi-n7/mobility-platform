import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0002_academicyear_closed_at"),
        ("imports", "0001_initial"),
        ("mobility", "0028_refactor_agreement_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="rawimport",
            name="academic_year",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="raw_imports",
                to="academic.academicyear",
                verbose_name="Année universitaire",
            ),
        ),
        migrations.AddField(
            model_name="rawimport",
            name="import_report",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="raw_imports",
                to="imports.importreport",
                verbose_name="Rapport d'import",
            ),
        ),
        migrations.AddIndex(
            model_name="rawimport",
            index=models.Index(
                fields=["import_report"], name="mobility_rawimport_report_idx"
            ),
        ),
        migrations.AlterModelOptions(
            name="rawimport",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Import brut",
                "verbose_name_plural": "Imports bruts",
            },
        ),
    ]
