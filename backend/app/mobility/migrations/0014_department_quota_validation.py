from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0013_move_level_to_reference"),
    ]

    operations = [
        migrations.AddField(
            model_name="departmentquota",
            name="estimated_places",
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="departmentquota",
            name="is_validated",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="departmentquota",
            name="validated_by",
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name="departmentquota",
            name="validated_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
