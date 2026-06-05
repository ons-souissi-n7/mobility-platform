from django.db import migrations


def populate_agreement_departments(apps, schema_editor):
    """Populate AgreementDepartment from existing Agreement.departments M2M."""
    Agreement = apps.get_model("mobility", "Agreement")
    AgreementDepartment = apps.get_model("mobility", "AgreementDepartment")

    for agreement in Agreement.objects.prefetch_related("departments").all():
        for department in agreement.departments.all():
            AgreementDepartment.objects.get_or_create(
                agreement=agreement,
                department=department,
            )


def populate_agreement_year_dept_fk(apps, schema_editor):
    """Populate agreement_department FK on AgreementYearDepartment."""
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
        ayd.agreement_department = ad
        ayd.save(update_fields=["agreement_department"])


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0033_agreement_department"),
    ]

    operations = [
        migrations.RunPython(
            populate_agreement_departments,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
