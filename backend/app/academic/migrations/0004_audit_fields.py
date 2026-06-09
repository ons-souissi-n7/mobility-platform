from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0003_alter_academicyear_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="academicyear",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="academicyear",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
