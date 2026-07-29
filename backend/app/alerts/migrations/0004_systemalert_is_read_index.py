from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("alerts", "0003_systemalert_academic_year"),
    ]

    operations = [
        migrations.AlterField(
            model_name="systemalert",
            name="is_read",
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
