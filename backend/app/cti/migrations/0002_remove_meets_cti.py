from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cti", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="mobilityduration",
            name="meets_cti",
        ),
    ]
