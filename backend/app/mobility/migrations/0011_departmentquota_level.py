import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0010_mobilitylevel_pegase_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="departmentquota",
            name="level",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="department_quotas",
                to="mobility.mobilitylevel",
            ),
        ),
    ]
