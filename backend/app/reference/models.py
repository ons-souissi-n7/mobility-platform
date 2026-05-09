from django.core.exceptions import ValidationError
from django.db import models


class CTIRegion(models.TextChoices):
    FRANCE = "france", "France"
    EUROPE_HORS_FRANCE = "europe_hors_france", "Europe (hors France)"
    CANADA_USA = "canada_usa", "Canada / États-Unis"
    AMERIQUE = "amerique", "Autres pays d'Amérique"
    ASIE_MOYEN_ORIENT = "asie_moyen_orient", "Asie / Moyen-Orient"
    AFRIQUE = "afrique", "Afrique"
    OCEANIE = "oceanie", "Océanie"


class Country(models.Model):
    """
    Referentiel stable des pays.

    La region CTI determine si un sejour compte pour le calcul CTI.
    """

    iso2 = models.CharField(
        max_length=2,
        unique=True,
        verbose_name="Code ISO 3166-1 alpha-2",
    )
    name_fr = models.CharField(max_length=100, verbose_name="Nom en francais")
    name_en = models.CharField(max_length=100, verbose_name="Nom en anglais")
    cti_region = models.CharField(
        max_length=20,
        choices=CTIRegion.choices,
        verbose_name="Region CTI",
    )

    class Meta:
        verbose_name = "Pays"
        verbose_name_plural = "Pays"
        ordering = ["name_fr"]

    def __str__(self) -> str:
        return f"{self.name_fr} ({self.iso2})"

    def clean(self) -> None:
        if self.iso2:
            self.iso2 = self.iso2.upper()
        if not self.iso2.isalpha() or len(self.iso2) != 2:
            raise ValidationError(
                {"iso2": "Le code ISO doit comporter exactement 2 lettres."}
            )


class Department(models.Model):
    """
    Departements pedagogiques de l'ENSEEIHT.

    Codes : SN, 3EA, MF2E
    """

    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code departement",
    )
    name = models.CharField(max_length=100, verbose_name="Intitule")

    class Meta:
        verbose_name = "Departement"
        verbose_name_plural = "Departements"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
