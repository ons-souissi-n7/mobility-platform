from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0007_student_pegase_sync"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="student",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="annualenrollment",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="annualenrollment",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="studentwish",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="studentwish",
            name="updated_by",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
