from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0029_rawimport_add_academic_year_and_report"),
        ("imports", "0003_migrate_rawimport_data"),
    ]

    operations = [
        migrations.DeleteModel(name="RawImport"),
    ]
