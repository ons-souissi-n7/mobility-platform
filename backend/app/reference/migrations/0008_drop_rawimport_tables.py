from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("reference", "0007_alter_country_id_alter_department_id_and_more"),
        ("imports", "0003_migrate_rawimport_data"),
    ]

    operations = [
        migrations.DeleteModel(name="DepartmentRawImport"),
        migrations.DeleteModel(name="LevelRawImport"),
    ]
