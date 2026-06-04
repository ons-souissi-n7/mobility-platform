import django.db.models.deletion
from django.db import migrations, models


def backfill_academic_year_fk(apps, schema_editor):
    """
    Lie les AgreementQuota/AgreementYearAvailability dont le FK academic_year
    est null à l'AcademicYear correspondante via le label (en essayant slash et tiret).
    Supprime les enregistrements dont l'année est introuvable.
    """
    AgreementQuota = apps.get_model("mobility", "AgreementQuota")
    AgreementYearAvailability = apps.get_model("mobility", "AgreementYearAvailability")
    AcademicYear = apps.get_model("academic", "AcademicYear")

    def resolve(label):
        yr = AcademicYear.objects.filter(label=label).first()
        if yr:
            return yr
        alt = label.replace("/", "-") if "/" in label else label.replace("-", "/")
        return AcademicYear.objects.filter(label=alt).first()

    for quota in AgreementQuota.objects.filter(academic_year__isnull=True):
        yr = resolve(quota.academic_year_label)
        if yr:
            quota.academic_year = yr
            quota.save(update_fields=["academic_year"])
        else:
            quota.delete()

    for avail in AgreementYearAvailability.objects.filter(academic_year__isnull=True):
        yr = resolve(avail.academic_year_label)
        if yr:
            avail.academic_year = yr
            avail.save(update_fields=["academic_year"])
        else:
            avail.delete()


class Migration(migrations.Migration):
    dependencies = [
        (
            "mobility",
            "0022_remove_mobilitycategory_mobility_mo_moveon__c7e278_idx_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(backfill_academic_year_fk, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="agreementquota",
            name="academic_year",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="agreement_quotas",
                to="academic.academicyear",
            ),
        ),
        migrations.AlterField(
            model_name="agreementyearavailability",
            name="academic_year",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="agreement_availabilities",
                to="academic.academicyear",
            ),
        ),
    ]
