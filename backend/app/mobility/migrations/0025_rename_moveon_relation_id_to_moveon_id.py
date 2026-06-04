from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0024_remove_departmentquota_level"),
    ]

    operations = [
        migrations.RenameField(
            model_name="agreement",
            old_name="moveon_relation_id",
            new_name="moveon_id",
        ),
    ]
