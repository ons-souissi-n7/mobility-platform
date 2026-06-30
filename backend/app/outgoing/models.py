from django.db import models
from django_fsm import FSMField, transition

from app.academic.models import AcademicYear
from app.core.models import TimeStampedModel


class AssignmentStatus(models.TextChoices):
    PROPOSED = "proposed", "Proposé"
    VALIDATED = "validated", "Validé"
    PUBLISHED = "published", "Publié"
    CANCELLED = "cancelled", "Annulé"


class SlotType(models.TextChoices):
    DEPT = "dept", "Slot département"
    SURPLUS = "surplus", "Slot surplus"
    ALTERNATIVE = "alternative", "Destination alternative"
    UNASSIGNED = "unassigned", "Non affecté"


class ResultSource(models.TextChoices):
    AUTO = "auto", "Auto-affectation"
    OVERRIDE = "override", "Correction manuelle"


class Assignment(TimeStampedModel):
    """Résultat d'un run de l'algorithme Gale-Shapley pour une année académique."""

    id = models.BigAutoField(primary_key=True)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    status = FSMField(
        max_length=20,
        default=AssignmentStatus.PROPOSED,
        choices=AssignmentStatus.choices,
        protected=True,
    )
    run_by = models.CharField(max_length=255, blank=True)
    override_reason = models.TextField(blank=True)

    total_students = models.IntegerField(default=0)
    assigned_count = models.IntegerField(default=0)
    unassigned_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Affectation"
        verbose_name_plural = "Affectations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["academic_year"], name="assignment_year_idx"),
            models.Index(fields=["status"], name="assignment_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Affectation {self.academic_year.label} ({self.status})"

    @transition(
        field=status,
        source=AssignmentStatus.PROPOSED,
        target=AssignmentStatus.VALIDATED,
    )
    def validate(self) -> None:
        pass

    @transition(
        field=status,
        source=AssignmentStatus.VALIDATED,
        target=AssignmentStatus.PUBLISHED,
    )
    def publish(self) -> None:
        pass

    @transition(
        field=status,
        source=[AssignmentStatus.PROPOSED, AssignmentStatus.VALIDATED],
        target=AssignmentStatus.CANCELLED,
    )
    def cancel(self) -> None:
        pass


class AssignmentResult(TimeStampedModel):
    """Résultat individuel d'affectation pour un étudiant."""

    id = models.BigAutoField(primary_key=True)
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="results",
    )
    annual_enrollment = models.ForeignKey(
        "students.AnnualEnrollment",
        on_delete=models.PROTECT,
        related_name="assignment_results",
    )
    agreement_year = models.ForeignKey(
        "mobility.AgreementYear",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assignment_results",
    )
    slot_type = models.CharField(
        max_length=20,
        choices=SlotType.choices,
        default=SlotType.UNASSIGNED,
    )
    assigned_rank = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Rang du vœu retenu"
    )
    override_reason = models.TextField(blank=True)
    override_agreement_year = models.ForeignKey(
        "mobility.AgreementYear",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="override_results",
    )
    override_slot_type = models.CharField(
        max_length=20,
        choices=SlotType.choices,
        null=True,
        blank=True,
        verbose_name="Type de slot (correction manuelle)",
    )
    override_rank = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Rang du vœu retenu (correction manuelle)",
    )
    source = models.CharField(
        max_length=20,
        choices=ResultSource.choices,
        default=ResultSource.AUTO,
    )

    class Meta:
        verbose_name = "Résultat d'affectation"
        verbose_name_plural = "Résultats d'affectation"
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "annual_enrollment"],
                name="unique_result_per_assignment_enrollment",
            )
        ]
        indexes = [
            models.Index(fields=["assignment"], name="result_assignment_idx"),
            models.Index(fields=["annual_enrollment"], name="result_enrollment_idx"),
            models.Index(fields=["agreement_year"], name="result_agreement_year_idx"),
            models.Index(fields=["slot_type"], name="result_slot_type_idx"),
            models.Index(fields=["source"], name="result_source_idx"),
        ]

    def __str__(self) -> str:
        if self.agreement_year:
            return f"{self.annual_enrollment.student} → {self.agreement_year} ({self.slot_type})"
        return f"{self.annual_enrollment.student} → non affecté"
