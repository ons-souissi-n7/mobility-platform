from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition

from app.core.models import TimeStampedModel


class AcademicYear(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)

    class CampaignStatus(models.TextChoices):
        INITIALIZATION = "initialization", "Initialisation"
        RECOMMENDATION = "recommendation", "Recommandation"
        CANDIDATURE = "candidature", "Candidature"
        IMPORT = "import", "Import"
        PRE_ASSIGNMENT = "pre_assignment", "Pré-affectation"
        VALIDATION = "validation", "Validation"
        PUBLISHED = "published", "Publiée"
        FINALIZATION = "finalization", "Finalisation CTI"
        CLOSED = "closed", "Clôturée"

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
            raise ValidationError(
                {"end_date": "La date de fin doit être postérieure à la date de début."}
            )

        if (
            self.wishes_open_date
            and self.wishes_close_date
            and self.wishes_open_date >= self.wishes_close_date
        ):
            raise ValidationError(
                {
                    "wishes_close_date": "La date de clôture des vœux doit être postérieure à la date d'ouverture."
                }
            )

        if (
            self.wishes_open_date
            and self.start_date
            and self.wishes_open_date < self.start_date
        ):
            raise ValidationError(
                {
                    "wishes_open_date": "La date d'ouverture des vœux ne peut pas être antérieure au début de l'année universitaire."
                }
            )

        if (
            self.wishes_close_date
            and self.end_date
            and self.wishes_close_date > self.end_date
        ):
            raise ValidationError(
                {
                    "wishes_close_date": "La date de clôture des vœux ne peut pas dépasser la fin de l'année universitaire."
                }
            )

    def _has_campaign_dates(self) -> bool:
        return bool(self.wishes_open_date and self.wishes_close_date)

    # ── Transitions ───────────────────────────────────────────────────────────

    @transition(
        field=status,
        source=CampaignStatus.INITIALIZATION,
        target=CampaignStatus.RECOMMENDATION,
        conditions=[_has_campaign_dates],
    )
    def open_recommendation(self) -> None:
        # Corps intentionnellement vide : @transition gère seul le changement d'état.
        pass

    @transition(
        field=status,
        source=CampaignStatus.RECOMMENDATION,
        target=CampaignStatus.CANDIDATURE,
    )
    def start_candidature(self) -> None:
        # Corps intentionnellement vide : @transition gère seul le changement d'état.
        pass

    @transition(
        field=status,
        source=CampaignStatus.CANDIDATURE,
        target=CampaignStatus.IMPORT,
    )
    def close_wishes(self) -> None:
        # Corps intentionnellement vide : @transition gère seul le changement d'état.
        pass

    @transition(
        field=status,
        source=CampaignStatus.IMPORT,
        target=CampaignStatus.PRE_ASSIGNMENT,
    )
    def launch_assignment(self) -> None:
        # Corps intentionnellement vide : @transition gère seul le changement d'état.
        pass

    @transition(
        field=status,
        source=CampaignStatus.PRE_ASSIGNMENT,
        target=CampaignStatus.VALIDATION,
    )
    def complete_assignment(self) -> None:
        # Corps intentionnellement vide : @transition gère seul le changement d'état.
        pass

    @transition(
        field=status,
        source=CampaignStatus.VALIDATION,
        target=CampaignStatus.PUBLISHED,
    )
    def publish_results(self) -> None:
        # Corps intentionnellement vide : @transition gère seul le changement d'état.
        pass

    @transition(
        field=status,
        source=CampaignStatus.PUBLISHED,
        target=CampaignStatus.FINALIZATION,
    )
    def finalize_cti(self) -> None:
        # Corps intentionnellement vide : @transition gère seul le changement d'état.
        pass

    @transition(
        field=status,
        source=CampaignStatus.FINALIZATION,
        target=CampaignStatus.CLOSED,
    )
    def close(self) -> None:
        self.closed_at = timezone.now()
        # Auto-resolve all open alerts linked to this year
        now = timezone.now()
        from app.alerts.models import SystemAlert  # noqa: PLC0415

        SystemAlert.objects.filter(academic_year=self, is_read=False).update(
            is_read=True, read_at=now
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

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
