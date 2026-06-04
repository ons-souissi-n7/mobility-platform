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

    id = models.BigAutoField(primary_key=True)
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

    Codes : SN, 3EA, MF2Ei
    """

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code departement",
    )
    name = models.CharField(max_length=100, verbose_name="Intitule")
    pegase_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Identifiant Pegase",
    )
    last_sync_pegase = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date dernier sync Pegase",
    )

    class Meta:
        verbose_name = "Departement"
        verbose_name_plural = "Departements"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Parcours(models.Model):
    id = models.BigAutoField(primary_key=True)
    department = models.ForeignKey(
        "Department",
        on_delete=models.PROTECT,
        related_name="parcours_list",
    )
    code = models.CharField(max_length=20)
    label = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Parcours"
        verbose_name_plural = "Parcours"
        unique_together = [("department", "code")]
        ordering = ["department", "code"]

    def __str__(self) -> str:
        return f"{self.department.code} — {self.label}"


class Level(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    pegase_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    last_sync_pegase = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Level"
        verbose_name_plural = "Levels"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}" if self.name else self.code
