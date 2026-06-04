from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0003_migrate_rawimport_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rawimport",
            name="entity",
            field=models.CharField(
                choices=[
                    ("department", "Département"),
                    ("level", "Niveau"),
                    ("partner_university", "Université partenaire"),
                    ("agreement_category", "Catégorie d'accord"),
                    ("agreement", "Accord"),
                    ("student", "Étudiant"),
                ],
                max_length=50,
            ),
        ),
    ]
