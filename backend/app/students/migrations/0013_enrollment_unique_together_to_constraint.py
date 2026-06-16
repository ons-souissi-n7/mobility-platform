from django.db import migrations, models


class Migration(migrations.Migration):
    """Replace deprecated unique_together with UniqueConstraint on AnnualEnrollment."""

    dependencies = [
        ("students", "0012_add_last_sync_to_enrollment_and_wish"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="annualenrollment",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="annualenrollment",
            constraint=models.UniqueConstraint(
                fields=["student", "academic_year"],
                name="unique_enrollment_student_year",
            ),
        ),
    ]
