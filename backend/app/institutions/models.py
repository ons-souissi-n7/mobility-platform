from django.db import models

from app.core.models import TimeStampedModel
from app.reference.models import Country


class PartnerUniversity(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    moveon_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100, blank=True)
    translated_name = models.CharField(max_length=255, blank=True)
    erasmus_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="universities",
    )
    last_sync_moveon = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Partner University"
        verbose_name_plural = "Partner Universities"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["moveon_id"]),
            models.Index(fields=["country"]),
            models.Index(fields=["name"], name="univ_name_idx"),
            models.Index(fields=["erasmus_code"], name="univ_erasmus_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.country.iso2})"

    def has_active_agreements(self) -> bool:
        return self.agreements.filter(year_instances__is_active=True).exists()


class PartnerUniversityRawImportStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IMPORTED = "imported", "Imported"
    FAILED = "failed", "Failed"
    IGNORED = "ignored", "Ignored"
    CONFLICT = "conflict", "Conflit"


class PartnerUniversityRawImport(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    source = models.CharField(max_length=255)
    source_file = models.CharField(max_length=255, blank=True)
    external_id = models.CharField(max_length=255)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=PartnerUniversityRawImportStatus.choices,
        default=PartnerUniversityRawImportStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Partner University Raw Import"
        verbose_name_plural = "Partner University Raw Imports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "external_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.source} - {self.external_id} ({self.status})"
