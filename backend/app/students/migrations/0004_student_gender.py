from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0003_alter_annualenrollment_id_alter_student_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("M", "Homme"), ("F", "Femme")],
                default="",
                max_length=1,
                verbose_name="Genre",
            ),
        ),
    ]
