import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0012_rename_mobilitylevel_level"),
        ("reference", "0004_copy_level_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agreementlevelconstraint",
            name="level",
            field=models.ForeignKey(
                "reference.Level",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="agreement_constraints",
            ),
        ),
        migrations.AlterField(
            model_name="departmentquota",
            name="level",
            field=models.ForeignKey(
                "reference.Level",
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="department_quotas",
                null=True,
                blank=True,
            ),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="Level"),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="DROP TABLE IF EXISTS mobility_level",
                    reverse_sql="",
                ),
            ],
        ),
    ]
