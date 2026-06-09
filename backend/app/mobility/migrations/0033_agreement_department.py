import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0032_audit_fields_remove_reference"),
        ("reference", "0008_audit_fields"),
    ]

    operations = [
        # Create AgreementDepartment table
        migrations.CreateModel(
            name="AgreementDepartment",
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
                ("remarks", models.TextField(blank=True)),
                (
                    "agreement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="agreement_departments",
                        to="mobility.agreement",
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="agreement_departments",
                        to="reference.department",
                    ),
                ),
            ],
            options={
                "verbose_name": "Agreement Department",
                "verbose_name_plural": "Agreement Departments",
                "ordering": ["department__code"],
            },
        ),
        migrations.AddConstraint(
            model_name="agreementdepartment",
            constraint=models.UniqueConstraint(
                fields=["agreement", "department"],
                name="unique_agreement_department",
            ),
        ),
        migrations.AddIndex(
            model_name="agreementdepartment",
            index=models.Index(
                fields=["agreement", "department"],
                name="mobility_ag_agreeme_dept_idx",
            ),
        ),
    ]
