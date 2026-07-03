from django.db import migrations, models


def populate_inp_total_places(apps, schema_editor):
    AgreementYear = apps.get_model("mobility", "AgreementYear")
    for ay in AgreementYear.objects.select_related("agreement").iterator():
        ay.inp_total_places = ay.agreement.inp_total_places
        ay.save(update_fields=["inp_total_places"])


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0040_agreementyeardepartment_adjusted_places"),
    ]

    operations = [
        migrations.AddField(
            model_name="agreementyear",
            name="inp_total_places",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(populate_inp_total_places, migrations.RunPython.noop),
    ]
