"""
Ajoute les colonnes created_by / updated_by manquantes sur cti_mobilityduration.

La migration 0001_initial inclut ces champs dans son état Django, mais la table
a pu être créée sans eux si elle a été appliquée avant que TimeStampedModel les
acquière. RunSQL avec IF NOT EXISTS est idempotent : aucun effet si les colonnes
existent déjà.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("cti", "0003_alter_mobilityduration_id"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE cti_mobilityduration ADD COLUMN IF NOT EXISTS created_by VARCHAR(255) NOT NULL DEFAULT ''",
                "ALTER TABLE cti_mobilityduration ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255) NOT NULL DEFAULT ''",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
