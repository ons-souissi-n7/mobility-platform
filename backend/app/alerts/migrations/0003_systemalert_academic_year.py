import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0008_add_finalization_status"),
        ("alerts", "0002_systemalert_acknowledged_usernames"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemalert",
            name="academic_year",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="alerts",
                to="academic.academicyear",
            ),
        ),
    ]
