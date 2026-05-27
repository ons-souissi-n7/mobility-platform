from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition

from app.core.models import TimeStampedModel


class AcademicYear(TimeStampedModel):
    class CampaignStatus(models.TextChoices):
        INITIALIZATION = "initialization", "Initialization"
        RECOMMENDATION = "recommendation", "Recommendation"
        CONSOLIDATION = "consolidation", "Consolidation"
        PRE_ASSIGNMENT = "pre_assignment", "Pre-Assignment"
        VALIDATION = "validation", "Validation"
        CLOSED = "closed", "Closed"

    label = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = FSMField(
        max_length=30,
        default=CampaignStatus.INITIALIZATION,
        choices=CampaignStatus.choices,
        protected=True,
    )
    wishes_open_date = models.DateField(null=True, blank=True)
    wishes_close_date = models.DateField(null=True, blank=True)
    gpa_freeze_date = models.DateField(null=True, blank=True)
    results_publication_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Academic Year"
        verbose_name_plural = "Academic Years"
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return self.label

    def full_clean(
        self,
        exclude=None,
        validate_unique=True,
        validate_constraints=True,
    ) -> None:
        clean_exclude = set(exclude or [])
        clean_exclude.add("status")
        super().full_clean(
            exclude=clean_exclude,
            validate_unique=validate_unique,
            validate_constraints=validate_constraints,
        )

    def clean(self) -> None:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({"end_date": "start_date must be before end_date"})

        if (
            self.wishes_open_date
            and self.wishes_close_date
            and self.wishes_open_date > self.wishes_close_date
        ):
            raise ValidationError(
                {
                    "wishes_close_date": (
                        "wishes_open_date must be before wishes_close_date"
                    )
                }
            )

    @transition(
        field=status,
        source=CampaignStatus.INITIALIZATION,
        target=CampaignStatus.RECOMMENDATION,
    )
    def open_recommendation(self) -> None:
        pass

    @transition(
        field=status,
        source=CampaignStatus.RECOMMENDATION,
        target=CampaignStatus.CONSOLIDATION,
    )
    def start_consolidation(self) -> None:
        pass

    @transition(
        field=status,
        source=CampaignStatus.CONSOLIDATION,
        target=CampaignStatus.PRE_ASSIGNMENT,
    )
    def launch_pre_assignment(self) -> None:
        pass

    @transition(
        field=status,
        source=CampaignStatus.PRE_ASSIGNMENT,
        target=CampaignStatus.VALIDATION,
    )
    def submit_for_validation(self) -> None:
        pass

    @transition(
        field=status,
        source=CampaignStatus.VALIDATION,
        target=CampaignStatus.CLOSED,
    )
    def close(self) -> None:
        self.closed_at = timezone.now()

    def is_active(self) -> bool:
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    def is_closed(self) -> bool:
        return self.status == self.CampaignStatus.CLOSED

    def is_wishes_open(self) -> bool:
        if not self.wishes_open_date or not self.wishes_close_date:
            return False

        today = timezone.now().date()
        return self.wishes_open_date <= today <= self.wishes_close_date

    @classmethod
    def get_current(cls):
        return (
            cls.objects.exclude(status=cls.CampaignStatus.CLOSED)
            .order_by("-start_date")
            .first()
        )

    @classmethod
    def detect_by_date(cls, date):
        return (
            cls.objects.filter(
                start_date__lte=date,
                end_date__gte=date,
            )
            .order_by("-start_date")
            .first()
        )
