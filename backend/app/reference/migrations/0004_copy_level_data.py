from django.db import migrations


def copy_levels_to_reference(apps, schema_editor):
    mob_level = apps.get_model("mobility", "Level")
    ref_level = apps.get_model("reference", "Level")
    mob_raw_import = apps.get_model("mobility", "RawImport")
    level_raw_import = apps.get_model("reference", "LevelRawImport")

    for level in mob_level.objects.all():
        ref_level.objects.create(
            id=level.id,
            code=level.code,
            name=level.name,
            is_active=level.is_active,
            pegase_id=level.pegase_id,
            last_sync_pegase=level.last_sync_pegase,
            created_at=level.created_at,
            updated_at=level.updated_at,
        )

    for ri in mob_raw_import.objects.filter(entity="mobility_level"):
        level_raw_import.objects.create(
            source=ri.source,
            source_file=ri.source_file,
            external_id=ri.external_id,
            payload=ri.payload,
            status=ri.status,
            error_message=ri.error_message,
            imported_at=ri.imported_at,
            created_at=ri.created_at,
            updated_at=ri.updated_at,
        )

    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('reference_level', 'id'), "
                "COALESCE((SELECT MAX(id) FROM reference_level), 1))"
            )


def reverse_copy(apps, schema_editor):
    ref_level = apps.get_model("reference", "Level")
    level_raw_import = apps.get_model("reference", "LevelRawImport")
    ref_level.objects.all().delete()
    level_raw_import.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("reference", "0003_level_levelrawimport"),
        ("mobility", "0012_rename_mobilitylevel_level"),
    ]

    operations = [
        migrations.RunPython(copy_levels_to_reference, reverse_code=reverse_copy),
    ]
