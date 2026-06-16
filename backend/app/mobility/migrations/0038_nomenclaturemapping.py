import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("institutions", "0006_partneruniversity_univ_name_idx_and_more"),
        ("mobility", "0037_agreement_agreement_name_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="NomenclatureMapping",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "updated_by",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "date_debut",
                    models.DateField(
                        blank=True, null=True, verbose_name="Date de début"
                    ),
                ),
                (
                    "date_fin",
                    models.DateField(blank=True, null=True, verbose_name="Date de fin"),
                ),
                (
                    "moveon_offer_name",
                    models.CharField(
                        help_text="Texte exact reçu dans le champ « Offre de séjour » lors du sync des vœux.",
                        max_length=500,
                        verbose_name="Nom de l'offre MoveON",
                    ),
                ),
                (
                    "agreement",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="nomenclature",
                        to="mobility.agreement",
                        verbose_name="Accord",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="nomenclature_mappings",
                        to="mobility.mobilitycategory",
                        verbose_name="Cadre de mobilité",
                    ),
                ),
                (
                    "partner_university",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="nomenclature_mappings",
                        to="institutions.partneruniversity",
                        verbose_name="Université partenaire",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nomenclature accord",
                "verbose_name_plural": "Nomenclature accords",
                "ordering": ["partner_university__name", "date_debut"],
            },
        ),
        migrations.AddIndex(
            model_name="nomenclaturemapping",
            index=models.Index(
                fields=["moveon_offer_name"], name="nomenclature_offer_name_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="nomenclaturemapping",
            index=models.Index(
                fields=["partner_university", "category"],
                name="nomenclature_univ_cat_idx",
            ),
        ),
    ]
