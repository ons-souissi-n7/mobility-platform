from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0003_agreement_moveon_unique_agreement_quota_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="agreementquota",
            name="is_estimated",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="agreementquota",
            name="estimation_basis",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="departmentquota",
            name="is_estimated",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="departmentquota",
            name="estimation_basis",
            field=models.TextField(blank=True),
        ),
    ]
