from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0009_alter_rawimport_entity_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="mobilitylevel",
            name="pegase_id",
            field=models.CharField(max_length=50, unique=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="mobilitylevel",
            name="last_sync_pegase",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
