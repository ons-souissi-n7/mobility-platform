from django.db import models

from app.reference.models import Country


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PartnerUniversity(TimeStampedModel):
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
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.country.iso2})"

    def has_active_agreements(self) -> bool:
        return self.agreements.filter(is_active=True).exists()
