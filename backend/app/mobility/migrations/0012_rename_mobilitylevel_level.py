from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0011_departmentquota_level"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="MobilityLevel",
            new_name="Level",
        ),
    ]
