import django.db.models.deletion
import django_fsm
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("academic", "0001_initial"),
        ("mobility", "0038_nomenclaturemapping"),
        ("students", "0017_assignment_add_created_updated_by"),
    ]

    operations = [
        # Supprimer les anciennes tables orphelines créées par students/0015
        migrations.RunSQL(
            sql=(
                "DROP TABLE IF EXISTS students_assignmentresult;"
                " DROP TABLE IF EXISTS students_assignment;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.CreateModel(
            name="Assignment",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
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
                    "academic_year",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignments",
                        to="academic.academicyear",
                    ),
                ),
                (
                    "status",
                    django_fsm.FSMField(
                        choices=[
                            ("proposed", "Proposé"),
                            ("validated", "Validé"),
                            ("published", "Publié"),
                            ("cancelled", "Annulé"),
                        ],
                        default="proposed",
                        max_length=20,
                        protected=True,
                    ),
                ),
                ("run_by", models.CharField(blank=True, max_length=255)),
                ("override_reason", models.TextField(blank=True)),
                ("total_students", models.IntegerField(default=0)),
                ("assigned_count", models.IntegerField(default=0)),
                ("unassigned_count", models.IntegerField(default=0)),
            ],
            options={
                "verbose_name": "Affectation",
                "verbose_name_plural": "Affectations",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(fields=["academic_year"], name="assignment_year_idx"),
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(fields=["status"], name="assignment_status_idx"),
        ),
        migrations.CreateModel(
            name="AssignmentResult",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
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
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="outgoing.assignment",
                    ),
                ),
                (
                    "annual_enrollment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignment_results",
                        to="students.annualenrollment",
                    ),
                ),
                (
                    "agreement_year",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignment_results",
                        to="mobility.agreementyear",
                    ),
                ),
                (
                    "slot_type",
                    models.CharField(
                        choices=[
                            ("dept", "Slot département"),
                            ("surplus", "Slot surplus"),
                            ("alternative", "Destination alternative"),
                            ("unassigned", "Non affecté"),
                        ],
                        default="unassigned",
                        max_length=20,
                    ),
                ),
                (
                    "assigned_rank",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Rang du vœu retenu",
                    ),
                ),
                ("override_reason", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Résultat d'affectation",
                "verbose_name_plural": "Résultats d'affectation",
            },
        ),
        migrations.AddConstraint(
            model_name="assignmentresult",
            constraint=models.UniqueConstraint(
                fields=["assignment", "annual_enrollment"],
                name="unique_result_per_assignment_enrollment",
            ),
        ),
        migrations.AddIndex(
            model_name="assignmentresult",
            index=models.Index(fields=["assignment"], name="result_assignment_idx"),
        ),
        migrations.AddIndex(
            model_name="assignmentresult",
            index=models.Index(fields=["annual_enrollment"], name="result_enrollment_idx"),
        ),
        migrations.AddIndex(
            model_name="assignmentresult",
            index=models.Index(fields=["agreement_year"], name="result_agreement_year_idx"),
        ),
        migrations.AddIndex(
            model_name="assignmentresult",
            index=models.Index(fields=["slot_type"], name="result_slot_type_idx"),
        ),
    ]
