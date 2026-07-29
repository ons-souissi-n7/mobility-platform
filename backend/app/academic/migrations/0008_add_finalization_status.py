import django_fsm
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0007_alter_academicyear_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="academicyear",
            name="status",
            field=django_fsm.FSMField(
                choices=[
                    ("initialization", "Initialisation"),
                    ("recommendation", "Recommandation"),
                    ("candidature", "Candidature"),
                    ("import", "Import"),
                    ("pre_assignment", "Pré-affectation"),
                    ("validation", "Validation"),
                    ("published", "Publiée"),
                    ("finalization", "Finalisation CTI"),
                    ("closed", "Clôturée"),
                ],
                default="initialization",
                max_length=30,
                protected=True,
            ),
        ),
    ]
