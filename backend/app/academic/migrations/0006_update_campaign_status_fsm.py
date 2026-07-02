from django.db import migrations, models


def migrate_status_forward(apps, schema_editor):
    """
    consolidation  → candidature
    pre_assignment → pre_assignment  (no change)
    validation     → validation      (no change)
    closed         → closed          (no change)
    """
    AcademicYear = apps.get_model("academic", "AcademicYear")
    AcademicYear.objects.filter(status="consolidation").update(status="candidature")


def migrate_status_backward(apps, schema_editor):
    AcademicYear = apps.get_model("academic", "AcademicYear")
    AcademicYear.objects.filter(status="candidature").update(status="consolidation")
    AcademicYear.objects.filter(status="import").update(status="consolidation")
    AcademicYear.objects.filter(status="published").update(status="validation")


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0005_remove_gpa_freeze_date_results_publication_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="academicyear",
            name="status",
            field=models.CharField(
                choices=[
                    ("initialization", "Initialisation"),
                    ("recommendation", "Recommandation"),
                    ("candidature", "Candidature"),
                    ("import", "Import"),
                    ("pre_assignment", "Pré-affectation"),
                    ("validation", "Validation"),
                    ("published", "Publiée"),
                    ("closed", "Clôturée"),
                ],
                default="initialization",
                max_length=30,
            ),
        ),
        migrations.RunPython(migrate_status_forward, migrate_status_backward),
    ]
