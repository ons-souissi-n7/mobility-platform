from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="academicyear",
            name="closed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
