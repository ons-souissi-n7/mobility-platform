from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0015_agreement_quota_validation"),
    ]

    operations = [
        migrations.AddField(
            model_name="agreementquota",
            name="source_institutions",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
