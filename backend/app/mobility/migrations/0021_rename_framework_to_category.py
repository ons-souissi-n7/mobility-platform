from django.db import migrations, models


def rename_entity_agreement_framework(apps, schema_editor):
    RawImport = apps.get_model("mobility", "RawImport")
    RawImport.objects.filter(entity="agreement_framework").update(
        entity="agreement_category"
    )


def reverse_rename_entity_agreement_framework(apps, schema_editor):
    RawImport = apps.get_model("mobility", "RawImport")
    RawImport.objects.filter(entity="agreement_category").update(
        entity="agreement_framework"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0020_remove_agreementlevelconstraint_agreement_and_more"),
    ]

    operations = [
        # MobilityCategory: moveon_framework_id → moveon_id
        migrations.RenameField(
            model_name="mobilitycategory",
            old_name="moveon_framework_id",
            new_name="moveon_id",
        ),
        # Agreement: framework (text) → category_name
        migrations.RenameField(
            model_name="agreement",
            old_name="framework",
            new_name="category_name",
        ),
        # Agreement: framework_ref (FK) → category
        migrations.RenameField(
            model_name="agreement",
            old_name="framework_ref",
            new_name="category",
        ),
        # RawImportEntity: update stored values in existing rows
        migrations.RunPython(
            rename_entity_agreement_framework,
            reverse_code=reverse_rename_entity_agreement_framework,
        ),
        # Update choices on the entity field
        migrations.AlterField(
            model_name="rawimport",
            name="entity",
            field=models.CharField(
                choices=[
                    ("partner_university", "Partner University"),
                    ("agreement_category", "Agreement Category"),
                    ("agreement", "Agreement"),
                    ("agreement_availability", "Agreement Availability"),
                    ("agreement_department", "Agreement Department"),
                    ("agreement_level", "Agreement Level"),
                    ("agreement_quota", "Agreement Quota"),
                    ("department_quota", "Department Quota"),
                    ("mobility_level", "Mobility Level"),
                ],
                default="partner_university",
                max_length=50,
            ),
        ),
    ]
