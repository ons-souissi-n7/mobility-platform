from django.db import models

from app.core.models import TimeStampedModel


class AlertLevel(models.TextChoices):
    WARNING = "warning", "Avertissement"
    ERROR = "error", "Erreur"


class SystemAlert(TimeStampedModel):
    level = models.CharField(
        max_length=20,
        choices=AlertLevel.choices,
        default=AlertLevel.WARNING,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    acknowledged_usernames = models.JSONField(default=list, blank=True)
    academic_year = models.ForeignKey(
        "academic.AcademicYear",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="alerts",
    )

    class Meta:
        verbose_name = "Alerte système"
        verbose_name_plural = "Alertes système"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.level}] {self.title}"
