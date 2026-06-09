import django.db.models.deletion
from django.db import migrations, models


def populate_annual_enrollment_fk(apps, schema_editor):
    """Set annual_enrollment FK from existing student + academic_year FKs.
    Wishes with no matching AnnualEnrollment are deleted (data integrity).
    """
    StudentWish = apps.get_model("students", "StudentWish")
    AnnualEnrollment = apps.get_model("students", "AnnualEnrollment")

    to_delete = []
    for wish in StudentWish.objects.all():
        enrollment = AnnualEnrollment.objects.filter(
            student_id=wish.student_id,
            academic_year_id=wish.academic_year_id,
        ).first()
        if enrollment is None:
            to_delete.append(wish.pk)
        else:
            wish.annual_enrollment_id = enrollment.pk
            wish.save(update_fields=["annual_enrollment_id"])

    if to_delete:
        StudentWish.objects.filter(pk__in=to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0008_audit_fields"),
    ]

    operations = [
        # Step 1: add annual_enrollment as nullable FK
        migrations.AddField(
            model_name="studentwish",
            name="annual_enrollment",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="wishes",
                to="students.annualenrollment",
            ),
        ),
        # Step 2: populate from existing student + academic_year
        migrations.RunPython(
            populate_annual_enrollment_fk,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 3: make it required
        migrations.AlterField(
            model_name="studentwish",
            name="annual_enrollment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="wishes",
                to="students.annualenrollment",
            ),
        ),
        # Step 4: remove old constraints and index on student + academic_year
        migrations.RemoveConstraint(
            model_name="studentwish",
            name="unique_student_wish_rank",
        ),
        migrations.RemoveConstraint(
            model_name="studentwish",
            name="unique_student_wish_agreement",
        ),
        migrations.RemoveIndex(
            model_name="studentwish",
            name="wish_student_year_idx",
        ),
        # Step 5: remove old student and academic_year FKs
        migrations.RemoveField(
            model_name="studentwish",
            name="student",
        ),
        migrations.RemoveField(
            model_name="studentwish",
            name="academic_year",
        ),
        # Step 6: add new constraints and index on annual_enrollment
        migrations.AddConstraint(
            model_name="studentwish",
            constraint=models.UniqueConstraint(
                fields=["annual_enrollment", "rank"],
                name="unique_wish_enrollment_rank",
            ),
        ),
        migrations.AddConstraint(
            model_name="studentwish",
            constraint=models.UniqueConstraint(
                fields=["annual_enrollment", "agreement"],
                name="unique_wish_enrollment_agreement",
            ),
        ),
        migrations.AddIndex(
            model_name="studentwish",
            index=models.Index(
                fields=["annual_enrollment"],
                name="wish_enrollment_idx",
            ),
        ),
    ]
