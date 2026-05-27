from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("mobility", "0014_department_quota_validation")]

    operations = [
        migrations.AddField(
            model_name="agreementquota",
            name="estimated_total_places",
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="agreementquota",
            name="is_validated",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="agreementquota",
            name="validated_by",
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name="agreementquota",
            name="validated_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
