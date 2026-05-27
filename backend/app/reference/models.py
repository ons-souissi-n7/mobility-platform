from django.core.exceptions import ValidationError
from django.db import models


class LevelRawImportStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IMPORTED = "imported", "Imported"
    FAILED = "failed", "Failed"
    IGNORED = "ignored", "Ignored"


class CTIRegion(models.TextChoices):
    FRANCE = "france", "France"
    EUROPE_HORS_FRANCE = "europe_hors_france", "Europe (hors France)"
    CANADA_USA = "canada_usa", "Canada / États-Unis"
    AMERIQUE = "amerique", "Autres pays d'Amérique"
    ASIE_MOYEN_ORIENT = "asie_moyen_orient", "Asie / Moyen-Orient"
    AFRIQUE = "afrique", "Afrique"
    OCEANIE = "oceanie", "Océanie"


class DepartmentRawImportStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IMPORTED = "imported", "Imported"
    FAILED = "failed", "Failed"
    IGNORED = "ignored", "Ignored"


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

    Codes : SN, 3EA, MF2Ei
    """

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


class DepartmentRawImport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.CharField(max_length=255)
    source_file = models.CharField(max_length=255, blank=True)
    external_id = models.CharField(max_length=255)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=DepartmentRawImportStatus.choices,
        default=DepartmentRawImportStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Department Raw Import"
        verbose_name_plural = "Department Raw Imports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "external_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.source} - {self.external_id} ({self.status})"


class Level(models.Model):
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


class LevelRawImport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.CharField(max_length=255)
    source_file = models.CharField(max_length=255, blank=True)
    external_id = models.CharField(max_length=255)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=LevelRawImportStatus.choices,
        default=LevelRawImportStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Level Raw Import"
        verbose_name_plural = "Level Raw Imports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "external_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.source} - {self.external_id} ({self.status})"
