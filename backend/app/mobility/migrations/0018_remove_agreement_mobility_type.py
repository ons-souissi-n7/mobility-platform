from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0017_rename_agreementframework_to_mobilitycategory"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="agreement",
            name="mobility_ag_mobilit_48f60c_idx",
        ),
        migrations.RemoveField(
            model_name="agreement",
            name="mobility_type",
        ),
    ]
