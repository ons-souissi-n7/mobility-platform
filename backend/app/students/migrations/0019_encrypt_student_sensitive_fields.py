from django.conf import settings
from django.db import migrations

import app.core.encrypted_fields


def _encrypt_columns(apps, schema_editor):
    """Convertit email et pegase_id de varchar à bytea chiffré via pgcrypto."""
    key = settings.PGCRYPTO_KEY
    c = schema_editor.connection
    with c.cursor() as cur:
        # email : varchar(254) → bytea
        cur.execute("ALTER TABLE students_student ADD COLUMN email_enc bytea")
        cur.execute(
            """
            UPDATE students_student
            SET email_enc = pgp_sym_encrypt(email, %s)
            WHERE email IS NOT NULL AND email <> ''
            """,
            [key],
        )
        cur.execute("ALTER TABLE students_student DROP COLUMN email")
        cur.execute("ALTER TABLE students_student RENAME COLUMN email_enc TO email")

        # pegase_id : varchar(255) → bytea
        cur.execute("ALTER TABLE students_student ADD COLUMN pegase_id_enc bytea")
        cur.execute(
            """
            UPDATE students_student
            SET pegase_id_enc = pgp_sym_encrypt(pegase_id, %s)
            WHERE pegase_id IS NOT NULL
            """,
            [key],
        )
        cur.execute("ALTER TABLE students_student DROP COLUMN pegase_id")
        cur.execute(
            "ALTER TABLE students_student RENAME COLUMN pegase_id_enc TO pegase_id"
        )


def _decrypt_columns(apps, schema_editor):
    """Rollback : redéchiffre et remet les colonnes en varchar."""
    key = settings.PGCRYPTO_KEY
    c = schema_editor.connection
    with c.cursor() as cur:
        cur.execute(
            "ALTER TABLE students_student ADD COLUMN email_plain varchar(254) DEFAULT ''"
        )
        cur.execute(
            """
            UPDATE students_student
            SET email_plain = pgp_sym_decrypt(email, %s)
            WHERE email IS NOT NULL
            """,
            [key],
        )
        cur.execute("ALTER TABLE students_student DROP COLUMN email")
        cur.execute("ALTER TABLE students_student RENAME COLUMN email_plain TO email")

        cur.execute(
            "ALTER TABLE students_student ADD COLUMN pegase_id_plain varchar(255)"
        )
        cur.execute(
            """
            UPDATE students_student
            SET pegase_id_plain = pgp_sym_decrypt(pegase_id, %s)
            WHERE pegase_id IS NOT NULL
            """,
            [key],
        )
        cur.execute("ALTER TABLE students_student DROP COLUMN pegase_id")
        cur.execute(
            "ALTER TABLE students_student RENAME COLUMN pegase_id_plain TO pegase_id"
        )


class Migration(migrations.Migration):
    """Chiffre les champs sensibles de Student (email, pegase_id) via pgcrypto."""

    dependencies = [
        ("students", "0018_enable_pgcrypto"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(_encrypt_columns, reverse_code=_decrypt_columns),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="student",
                    name="email",
                    field=app.core.encrypted_fields.PgEncryptedTextField(blank=True),
                ),
                migrations.AlterField(
                    model_name="student",
                    name="pegase_id",
                    field=app.core.encrypted_fields.PgEncryptedTextField(
                        blank=True,
                        null=True,
                        verbose_name="Identifiant Pégase",
                    ),
                ),
            ],
        ),
    ]
