from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0023_make_academic_year_fk_required"),
        ("reference", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="departmentquota",
            name="level",
        ),
    ]
