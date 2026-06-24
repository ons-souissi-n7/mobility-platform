import django.db.models.deletion
from django.db import migrations, models


def _populate_agreement_year(apps, schema_editor):
    """
    Pour chaque vœu existant, trouve l'AgreementYear correspondant
    (même accord + même année académique que l'inscription).
    Les vœux sans AgreementYear sont supprimés (cas impossible en pratique
    car initialize_new_year_mobility crée les slots à l'init de chaque année).
    """
    StudentWish = apps.get_model("students", "StudentWish")
    AgreementYear = apps.get_model("mobility", "AgreementYear")

    orphans = []
    for wish in StudentWish.objects.select_related(
        "agreement", "annual_enrollment__academic_year"
    ).all():
        academic_year = wish.annual_enrollment.academic_year
        try:
            wish.agreement_year = AgreementYear.objects.get(
                agreement=wish.agreement, academic_year=academic_year
            )
            wish.save(update_fields=["agreement_year"])
        except AgreementYear.DoesNotExist:
            orphans.append(wish.pk)

    if orphans:
        StudentWish.objects.filter(pk__in=orphans).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("mobility", "0038_nomenclaturemapping"),
        ("students", "0013_enrollment_unique_together_to_constraint"),
    ]

    operations = [
        # 1. Ajout nullable pour pouvoir insérer la valeur avant de contraindre
        migrations.AddField(
            model_name="studentwish",
            name="agreement_year",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="student_wishes",
                to="mobility.agreementyear",
            ),
        ),
        # 2. Remplissage des données existantes
        migrations.RunPython(
            _populate_agreement_year,
            reverse_code=migrations.RunPython.noop,
        ),
        # 3. Suppression ancienne contrainte unique (annual_enrollment, agreement)
        migrations.RemoveConstraint(
            model_name="studentwish",
            name="unique_wish_enrollment_agreement",
        ),
        # 4. Suppression ancien index sur agreement
        migrations.RemoveIndex(
            model_name="studentwish",
            name="wish_agreement_idx",
        ),
        # 5. Suppression ancien FK agreement
        migrations.RemoveField(
            model_name="studentwish",
            name="agreement",
        ),
        # 6. Passage NOT NULL maintenant que toutes les lignes sont remplies
        migrations.AlterField(
            model_name="studentwish",
            name="agreement_year",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="student_wishes",
                to="mobility.agreementyear",
            ),
        ),
        # 7. Nouvelle contrainte unique (annual_enrollment, agreement_year)
        migrations.AddConstraint(
            model_name="studentwish",
            constraint=models.UniqueConstraint(
                fields=["annual_enrollment", "agreement_year"],
                name="unique_wish_enrollment_agreement_year",
            ),
        ),
        # 8. Nouvel index sur agreement_year
        migrations.AddIndex(
            model_name="studentwish",
            index=models.Index(
                fields=["agreement_year"],
                name="wish_agreement_year_idx",
            ),
        ),
    ]
