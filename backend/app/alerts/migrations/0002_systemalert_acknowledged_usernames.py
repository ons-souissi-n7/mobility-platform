from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("alerts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemalert",
            name="acknowledged_usernames",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
