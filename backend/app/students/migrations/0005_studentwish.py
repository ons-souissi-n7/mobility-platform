import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0003_alter_academicyear_id"),
        ("mobility", "0031_alter_mobilitycategory_options_and_more"),
        ("students", "0004_student_gender"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentWish",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "rank",
                    models.PositiveSmallIntegerField(verbose_name="Rang du vœu"),
                ),
                (
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="student_wishes",
                        to="academic.academicyear",
                    ),
                ),
                (
                    "agreement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="student_wishes",
                        to="mobility.agreement",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishes",
                        to="students.student",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vœu étudiant",
                "verbose_name_plural": "Vœux étudiants",
                "ordering": ["student__last_name", "academic_year", "rank"],
            },
        ),
        migrations.AddConstraint(
            model_name="studentwish",
            constraint=models.UniqueConstraint(
                fields=["student", "academic_year", "rank"],
                name="unique_student_wish_rank",
            ),
        ),
        migrations.AddConstraint(
            model_name="studentwish",
            constraint=models.UniqueConstraint(
                fields=["student", "academic_year", "agreement"],
                name="unique_student_wish_agreement",
            ),
        ),
        migrations.AddIndex(
            model_name="studentwish",
            index=models.Index(
                fields=["student", "academic_year"],
                name="wish_student_year_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="studentwish",
            index=models.Index(
                fields=["agreement"],
                name="wish_agreement_idx",
            ),
        ),
    ]
