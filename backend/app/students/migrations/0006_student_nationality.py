import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reference", "0008_drop_rawimport_tables"),
        ("students", "0005_studentwish"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="nationality",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="students",
                to="reference.country",
                verbose_name="Nationalité",
            ),
        ),
    ]
