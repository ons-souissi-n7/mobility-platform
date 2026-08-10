from django.db import migrations


class Migration(migrations.Migration):
    """Active l'extension PostgreSQL pgcrypto nécessaire au chiffrement des champs sensibles."""

    dependencies = [
        ("students", "0017_assignment_add_created_updated_by"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pgcrypto;",
            reverse_sql="DROP EXTENSION IF EXISTS pgcrypto;",
        ),
    ]
