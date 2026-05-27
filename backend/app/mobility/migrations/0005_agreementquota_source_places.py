from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0004_quota_estimation_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="agreementquota",
            name="source_total_places",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="agreementquota",
            name="source_remaining_places",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="agreementquota",
            name="source_scope",
            field=models.CharField(default="inp", max_length=50),
        ),
    ]
