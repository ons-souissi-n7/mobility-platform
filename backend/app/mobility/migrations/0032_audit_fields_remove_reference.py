from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0031_alter_mobilitycategory_options_and_more"),
    ]

    operations = [
        # Add created_by/updated_by to all existing mobility models
        migrations.AddField(
            model_name="mobilitycategory",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="mobilitycategory",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="agreement",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="agreement",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="agreementyear",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="agreementyear",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="agreementyeardepartment",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="agreementyeardepartment",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        # Remove reference field from Agreement
        migrations.RemoveField(
            model_name="agreement",
            name="reference",
        ),
    ]
