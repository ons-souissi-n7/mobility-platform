from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0039_alter_nomenclaturemapping_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="agreementyeardepartment",
            name="adjusted_places",
            field=models.IntegerField(
                blank=True,
                help_text="Remplace le quota estimé quand renseigné manuellement.",
                null=True,
                verbose_name="Quota ajusté N7",
            ),
        ),
    ]
