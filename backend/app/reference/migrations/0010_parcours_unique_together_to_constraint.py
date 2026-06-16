from django.db import migrations, models


class Migration(migrations.Migration):
    """Replace deprecated unique_together with UniqueConstraint on Parcours."""

    dependencies = [
        ("reference", "0009_merge_0008_audit_fields_0008_drop_rawimport_tables"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="parcours",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="parcours",
            constraint=models.UniqueConstraint(
                fields=["department", "code"],
                name="unique_parcours_dept_code",
            ),
        ),
    ]
