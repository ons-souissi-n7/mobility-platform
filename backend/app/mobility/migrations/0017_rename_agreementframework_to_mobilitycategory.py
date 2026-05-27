from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0016_agreementquota_source_institutions"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="AgreementFramework",
            new_name="MobilityCategory",
        ),
    ]
