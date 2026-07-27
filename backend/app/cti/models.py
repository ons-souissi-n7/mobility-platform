from django.db import models

from app.core.models import TimeStampedModel


class MobilityDuration(TimeStampedModel):
    """Durée CTI calculée et persistée pour un étudiant."""

    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="cti_duration",
        verbose_name="Étudiant",
    )
    exchange_weeks = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0,
        verbose_name="Échange universitaire (sem.)",
    )
    internship_weeks = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0,
        verbose_name="Stage international (sem.)",
    )
    complementary_weeks = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0,
        verbose_name="Mobilité complémentaire (sem.)",
    )
    total_weeks = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0,
        verbose_name="Total (sem.)",
    )

    class Meta:
        verbose_name = "Durée CTI"
        verbose_name_plural = "Durées CTI"
        ordering = ["-total_weeks"]

    def __str__(self) -> str:
        return f"{self.student} — {self.total_weeks} sem."
