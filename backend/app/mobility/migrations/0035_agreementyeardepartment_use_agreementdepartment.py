import django.db.models.deletion
from django.db import migrations, models


def populate_agreement_department_fk(apps, schema_editor):
    """Set agreement_department FK from existing department FK."""
    AgreementYearDepartment = apps.get_model("mobility", "AgreementYearDepartment")
    AgreementDepartment = apps.get_model("mobility", "AgreementDepartment")

    for ayd in AgreementYearDepartment.objects.select_related(
        "agreement_year__agreement", "department"
    ).all():
        ad = AgreementDepartment.objects.filter(
            agreement=ayd.agreement_year.agreement,
            department=ayd.department,
        ).first()
        if ad is None:
            ad = AgreementDepartment.objects.create(
                agreement=ayd.agreement_year.agreement,
                department=ayd.department,
            )
        ayd.agreement_department_id = ad.id
        ayd.save(update_fields=["agreement_department_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0034_migrate_to_agreement_department"),
    ]

    operations = [
        # Step 1: add agreement_department as nullable FK
        migrations.AddField(
            model_name="agreementyeardepartment",
            name="agreement_department",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="year_quotas",
                to="mobility.agreementdepartment",
            ),
        ),
        # Step 2: populate it via data migration
        migrations.RunPython(
            populate_agreement_department_fk,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 3: enforce NOT NULL via SQL (avoids Postgres "pending trigger events" issue
        # that occurs when Django's AlterField reconstructs the column after RunPython in same tx)
        migrations.RunSQL(
            "ALTER TABLE mobility_agreementyeardepartment ALTER COLUMN agreement_department_id SET NOT NULL",
            reverse_sql="ALTER TABLE mobility_agreementyeardepartment ALTER COLUMN agreement_department_id DROP NOT NULL",
        ),
        # Step 4: update Django state to reflect NOT NULL (DB already done in step 3)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="agreementyeardepartment",
                    name="agreement_department",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="year_quotas",
                        to="mobility.agreementdepartment",
                    ),
                ),
            ],
            database_operations=[],
        ),
        # Step 5: remove old unique constraint (conditional: may be missing if DB state drifted)
        migrations.RunSQL(
            """
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'unique_agreement_year_department'
                    AND conrelid = 'mobility_agreementyeardepartment'::regclass
                ) THEN
                    ALTER TABLE mobility_agreementyeardepartment
                        DROP CONSTRAINT unique_agreement_year_department;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="agreementyeardepartment",
                    name="unique_agreement_year_department",
                ),
            ],
            database_operations=[],
        ),
        # Step 6: remove old index
        migrations.RunSQL(
            """
            DO $$ BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE indexname = 'mobility_ag_agreeme_0ad96d_idx'
                ) THEN
                    DROP INDEX mobility_ag_agreeme_0ad96d_idx;
                END IF;
            END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveIndex(
                    model_name="agreementyeardepartment",
                    name="mobility_ag_agreeme_0ad96d_idx",
                ),
            ],
            database_operations=[],
        ),
        # Step 7: remove old department FK
        migrations.RemoveField(
            model_name="agreementyeardepartment",
            name="department",
        ),
        # Step 8: add new unique constraint and index on agreement_department
        migrations.AddConstraint(
            model_name="agreementyeardepartment",
            constraint=models.UniqueConstraint(
                fields=["agreement_year", "agreement_department"],
                name="unique_agreement_year_department",
            ),
        ),
        migrations.AddIndex(
            model_name="agreementyeardepartment",
            index=models.Index(
                fields=["agreement_year", "agreement_department"],
                name="mobility_ag_agreeme_ayd_idx",
            ),
        ),
        # Step 9: remove Agreement.departments M2M (now replaced by AgreementDepartment)
        migrations.RemoveField(
            model_name="agreement",
            name="departments",
        ),
    ]
