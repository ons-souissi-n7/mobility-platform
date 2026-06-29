from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0004_audit_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="academicyear",
            name="gpa_freeze_date",
        ),
        migrations.RemoveField(
            model_name="academicyear",
            name="results_publication_date",
        ),
    ]
