"""
Data migration: copy existing raw import records from the three separate tables
(reference.DepartmentRawImport, reference.LevelRawImport, mobility.RawImport)
into the new central imports.RawImport table.
"""

from django.db import migrations


def copy_rawimport_data(apps, schema_editor):
    RawImport = apps.get_model("imports", "RawImport")

    # -- Departments (reference.DepartmentRawImport -> entity=department) ----
    DepartmentRawImport = apps.get_model("reference", "DepartmentRawImport")
    for old in DepartmentRawImport.objects.all():
        RawImport.objects.create(
            source=old.source,
            source_file=old.source_file,
            external_id=old.external_id,
            payload=old.payload,
            entity="department",
            status=old.status,
            error_message=old.error_message,
            imported_at=old.imported_at,
            created_at=old.created_at,
            updated_at=old.updated_at,
        )

    # -- Levels (reference.LevelRawImport -> entity=level) -------------------
    LevelRawImport = apps.get_model("reference", "LevelRawImport")
    for old in LevelRawImport.objects.all():
        RawImport.objects.create(
            source=old.source,
            source_file=old.source_file,
            external_id=old.external_id,
            payload=old.payload,
            entity="level",
            status=old.status,
            error_message=old.error_message,
            imported_at=old.imported_at,
            created_at=old.created_at,
            updated_at=old.updated_at,
        )

    # -- Mobility (mobility.RawImport -> entity kept as-is) ------------------
    mobility_raw_import = apps.get_model("mobility", "RawImport")
    for old in mobility_raw_import.objects.all():
        RawImport.objects.create(
            source=old.source,
            source_file=old.source_file,
            external_id=old.external_id,
            payload=old.payload,
            entity=old.entity,
            status=old.status,
            error_message=old.error_message,
            imported_at=old.imported_at,
            academic_year=old.academic_year,
            import_report=old.import_report,
            created_at=old.created_at,
            updated_at=old.updated_at,
        )


def reverse_migration(apps, schema_editor):
    RawImport = apps.get_model("imports", "RawImport")
    RawImport.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0002_rawimport"),
        ("reference", "0007_alter_country_id_alter_department_id_and_more"),
        ("mobility", "0029_rawimport_add_academic_year_and_report"),
    ]

    operations = [
        migrations.RunPython(copy_rawimport_data, reverse_migration),
    ]
