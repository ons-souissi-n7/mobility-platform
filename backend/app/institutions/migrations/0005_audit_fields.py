from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("institutions", "0004_alter_partneruniversity_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="partneruniversity",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="partneruniversity",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="partneruniversityrawimport",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="partneruniversityrawimport",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
