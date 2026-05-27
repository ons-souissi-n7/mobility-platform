# Generated manually for mobility agreement and quota business rules.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "mobility",
            "0002_alter_agreement_options_alter_agreementquota_options_and_more",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE mobility_rawimport "
                        "ADD COLUMN IF NOT EXISTS entity varchar(50) "
                        "NOT NULL DEFAULT 'partner_university'"
                    ),
                    reverse_sql=(
                        "ALTER TABLE mobility_rawimport DROP COLUMN IF EXISTS entity"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="rawimport",
                    name="entity",
                    field=models.CharField(
                        choices=[
                            ("partner_university", "Partner University"),
                            ("agreement", "Agreement"),
                            ("agreement_quota", "Agreement Quota"),
                            ("department_quota", "Department Quota"),
                        ],
                        default="partner_university",
                        max_length=50,
                    ),
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE mobility_agreement
                    ALTER COLUMN moveon_relation_id TYPE varchar(255);
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conname = 'mobility_agreement_moveon_relation_id_key'
                        ) THEN
                            ALTER TABLE mobility_agreement
                            ADD CONSTRAINT mobility_agreement_moveon_relation_id_key
                            UNIQUE (moveon_relation_id);
                        END IF;
                    END
                    $$;
                    """,
                    reverse_sql="""
                    ALTER TABLE mobility_agreement
                    DROP CONSTRAINT IF EXISTS mobility_agreement_moveon_relation_id_key;
                    """,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="agreement",
                    name="moveon_relation_id",
                    field=models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        unique=True,
                    ),
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conname = 'unique_agreement_quota_period'
                        ) THEN
                            ALTER TABLE mobility_agreementquota
                            ADD CONSTRAINT unique_agreement_quota_period
                            UNIQUE (
                                agreement_id,
                                academic_year_label,
                                period
                            );
                        END IF;
                    END
                    $$;
                    """,
                    reverse_sql=(
                        "ALTER TABLE mobility_agreementquota "
                        "DROP CONSTRAINT IF EXISTS unique_agreement_quota_period"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="agreementquota",
                    constraint=models.UniqueConstraint(
                        fields=("agreement", "academic_year_label", "period"),
                        name="unique_agreement_quota_period",
                    ),
                ),
            ],
        ),
    ]
