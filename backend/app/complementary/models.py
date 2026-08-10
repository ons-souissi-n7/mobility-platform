from django.db import models
from django_fsm import FSMField, transition

from app.core.models import TimeStampedModel


class MobilityStatus(models.TextChoices):
    PENDING = "pending", "En attente de validation"
    VALIDATED = "validated", "Validée"
    REJECTED = "rejected", "Rejetée"


class ComplementaryMobility(TimeStampedModel):
    """Déclaration de mobilité complémentaire déposée par un étudiant."""

    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="complementary_mobilities",
    )
    academic_year = models.ForeignKey(
        "academic.AcademicYear",
        on_delete=models.PROTECT,
        related_name="complementary_mobilities",
    )
    experience_type = models.CharField(
        max_length=100,
        verbose_name="Type d'expérience",
        help_text="Ex : Summer school, séjour linguistique, programme court…",
    )
    destination_country = models.ForeignKey(
        "reference.Country",
        on_delete=models.PROTECT,
        related_name="complementary_mobilities",
    )
    destination_institution = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    document_key = models.CharField(
        max_length=512,
        blank=True,
        help_text="Clé objet MinIO du justificatif déposé",
    )
    document_name = models.CharField(max_length=255, blank=True)
    status = FSMField(
        max_length=20,
        default=MobilityStatus.PENDING,
        choices=MobilityStatus.choices,
        protected=True,
    )
    rejection_reason = models.TextField(blank=True)
    document_retention_until = models.DateField(
        null=True,
        blank=True,
        verbose_name="Conserver le justificatif jusqu'au",
        help_text="Date d'expiration du délai de conservation RGPD ; après cette date le fichier est supprimé automatiquement.",
    )

    class Meta:
        verbose_name = "Mobilité complémentaire"
        verbose_name_plural = "Mobilités complémentaires"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student"], name="compl_mob_student_idx"),
            models.Index(fields=["status"], name="compl_mob_status_idx"),
            models.Index(fields=["academic_year"], name="compl_mob_year_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.student} — {self.experience_type} ({self.status})"

    @transition(
        field=status,
        source=MobilityStatus.PENDING,
        target=MobilityStatus.VALIDATED,
    )
    def validate(self) -> None:
        pass

    @transition(
        field=status,
        source=MobilityStatus.PENDING,
        target=MobilityStatus.REJECTED,
    )
    def reject(self, reason: str) -> None:
        self.rejection_reason = reason
