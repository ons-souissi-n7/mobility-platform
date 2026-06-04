from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="student",
            name="pegase_id",
        ),
    ]
