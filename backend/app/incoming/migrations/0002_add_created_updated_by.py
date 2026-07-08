from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("incoming", "0001_initial"),
    ]

    operations = [
        # ADD COLUMN IF NOT EXISTS — safe even if columns were added manually
        migrations.RunSQL(
            sql="""
                ALTER TABLE incoming_incomingstudent
                    ADD COLUMN IF NOT EXISTS created_by VARCHAR(255) NOT NULL DEFAULT '',
                    ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255) NOT NULL DEFAULT '';
            """,
            reverse_sql="""
                ALTER TABLE incoming_incomingstudent
                    DROP COLUMN IF EXISTS created_by,
                    DROP COLUMN IF EXISTS updated_by;
            """,
            state_operations=[
                migrations.AddField(
                    model_name="incomingstudent",
                    name="created_by",
                    field=models.CharField(blank=True, default="", max_length=255),
                ),
                migrations.AddField(
                    model_name="incomingstudent",
                    name="updated_by",
                    field=models.CharField(blank=True, default="", max_length=255),
                ),
            ],
        ),
    ]
