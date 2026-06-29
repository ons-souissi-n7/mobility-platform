import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0039_alter_nomenclaturemapping_id"),
        ("outgoing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignmentresult",
            name="override_agreement_year",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="override_results",
                to="mobility.agreementyear",
            ),
        ),
        migrations.AddField(
            model_name="assignmentresult",
            name="source",
            field=models.CharField(
                choices=[
                    ("auto", "Auto-affectation"),
                    ("override", "Correction manuelle"),
                ],
                default="auto",
                max_length=20,
            ),
        ),
        migrations.AddIndex(
            model_name="assignmentresult",
            index=models.Index(fields=["source"], name="result_source_idx"),
        ),
    ]
