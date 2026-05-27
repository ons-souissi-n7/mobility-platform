from django.core.exceptions import ValidationError
from django.db import models

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.reference.models import Department, Level


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class RawImportStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IMPORTED = "imported", "Imported"
    FAILED = "failed", "Failed"
    IGNORED = "ignored", "Ignored"


class RawImportEntity(models.TextChoices):
    PARTNER_UNIVERSITY = "partner_university", "Partner University"
    AGREEMENT_FRAMEWORK = "agreement_framework", "Agreement Framework"
    AGREEMENT = "agreement", "Agreement"
    AGREEMENT_AVAILABILITY = "agreement_availability", "Agreement Availability"
    AGREEMENT_DEPARTMENT = "agreement_department", "Agreement Department"
    AGREEMENT_LEVEL = "agreement_level", "Agreement Level"
    AGREEMENT_QUOTA = "agreement_quota", "Agreement Quota"
    DEPARTMENT_QUOTA = "department_quota", "Department Quota"
    MOBILITY_LEVEL = "mobility_level", "Mobility Level"


class RawImport(TimeStampedModel):
    source = models.CharField(max_length=255)
    source_file = models.CharField(max_length=255, blank=True)
    external_id = models.CharField(max_length=255)
    payload = models.JSONField()
    entity = models.CharField(
        max_length=50,
        choices=RawImportEntity.choices,
        default=RawImportEntity.PARTNER_UNIVERSITY,
    )
    status = models.CharField(
        max_length=20,
        choices=RawImportStatus.choices,
        default=RawImportStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Raw Import"
        verbose_name_plural = "Raw Imports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "external_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.source} - {self.external_id} ({self.status})"


class MobilityCategory(TimeStampedModel):
    moveon_framework_id = models.CharField(max_length=255, unique=True)
    external_id = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255)
    relation_types = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    last_sync_moveon = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Mobility Category"
        verbose_name_plural = "Mobility Categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["moveon_framework_id"]),
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name


class Agreement(TimeStampedModel):
    moveon_relation_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    reference = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255)
    partner_university = models.ForeignKey(
        PartnerUniversity,
        on_delete=models.PROTECT,
        related_name="agreements",
    )
    relation_type = models.CharField(max_length=100, blank=True)
    framework = models.CharField(max_length=100, blank=True)
    framework_ref = models.ForeignKey(
        MobilityCategory,
        on_delete=models.PROTECT,
        related_name="agreements",
        null=True,
        blank=True,
    )
    direction = models.CharField(max_length=50, default="unknown")
    status = models.CharField(max_length=50, default="draft")
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    start_academic_year = models.CharField(max_length=20, blank=True)
    end_academic_year = models.CharField(max_length=20, blank=True)
    discipline = models.CharField(max_length=255, blank=True)
    isced = models.CharField(max_length=50, blank=True)
    level = models.CharField(max_length=100, blank=True)
    formation = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    restrictions = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    last_sync_moveon = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Agreement"
        verbose_name_plural = "Agreements"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["partner_university", "is_active"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.partner_university.name}"

    def clean(self) -> None:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({"end_date": "start_date must be before end_date"})


class AgreementYearAvailability(TimeStampedModel):
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="year_availabilities",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="agreement_availabilities",
        null=True,
        blank=True,
    )
    academic_year_label = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)
    source = models.CharField(max_length=50, default="manual")
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Agreement Year Availability"
        verbose_name_plural = "Agreement Year Availabilities"
        ordering = ["academic_year_label", "agreement__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "academic_year_label"],
                name="unique_agreement_year_availability",
            ),
        ]
        indexes = [
            models.Index(fields=["academic_year_label", "is_available"]),
            models.Index(fields=["agreement", "academic_year"]),
        ]

    def __str__(self) -> str:
        status = "available" if self.is_available else "unavailable"
        return f"{self.agreement.name} - {self.academic_year_label} ({status})"


class AgreementDepartmentConstraint(TimeStampedModel):
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="department_constraints",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="agreement_constraints",
    )
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=50, default="manual")
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Agreement Department Constraint"
        verbose_name_plural = "Agreement Department Constraints"
        ordering = ["agreement__name", "department__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "department"],
                name="unique_agreement_department_constraint",
            ),
        ]
        indexes = [
            models.Index(fields=["agreement", "is_active"]),
            models.Index(fields=["department", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.agreement.name} - {self.department.code}"


class AgreementLevelConstraint(TimeStampedModel):
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="level_constraints",
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.PROTECT,
        related_name="agreement_constraints",
    )
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=50, default="manual")
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Agreement Level Constraint"
        verbose_name_plural = "Agreement Level Constraints"
        ordering = ["agreement__name", "level__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "level"],
                name="unique_agreement_level_constraint",
            ),
        ]
        indexes = [
            models.Index(fields=["agreement", "is_active"]),
            models.Index(fields=["level", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.agreement.name} - {self.level.code}"


class AgreementQuota(TimeStampedModel):
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="quotas",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="agreement_quotas",
        null=True,
        blank=True,
    )
    academic_year_label = models.CharField(max_length=20)
    period = models.CharField(max_length=100, blank=True)
    places_id = models.CharField(max_length=255, blank=True, null=True)  # noqa: DJ001
    source_total_places = models.IntegerField(null=True, blank=True)
    source_remaining_places = models.IntegerField(null=True, blank=True)
    source_scope = models.CharField(max_length=50, default="inp")
    source_institutions = models.CharField(max_length=500, blank=True)
    total_places = models.IntegerField(default=0)
    remaining_places = models.IntegerField(default=0)
    total_duration = models.IntegerField(null=True, blank=True)
    duration_unit = models.CharField(max_length=50, blank=True)
    is_effective = models.BooleanField(default=True)
    is_estimated = models.BooleanField(default=False)
    estimated_total_places = models.IntegerField(null=True, blank=True)
    is_validated = models.BooleanField(default=False)
    validated_by = models.CharField(max_length=255, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    estimation_basis = models.TextField(blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Agreement Quota"
        verbose_name_plural = "Agreement Quotas"
        ordering = ["academic_year_label"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "academic_year_label", "period"],
                name="unique_agreement_quota_period",
            ),
        ]
        indexes = [
            models.Index(fields=["agreement", "academic_year"]),
        ]

    def __str__(self) -> str:
        return f"{self.agreement.name} ({self.academic_year_label})"

    def clean(self) -> None:
        errors = {}

        if self.total_places < 0:
            errors["total_places"] = "total_places cannot be negative"
        if self.remaining_places < 0:
            errors["remaining_places"] = "remaining_places cannot be negative"
        if self.total_duration is not None and self.total_duration < 0:
            errors["total_duration"] = "total_duration cannot be negative"
        if self.remaining_places > self.total_places:
            errors["remaining_places"] = "remaining_places cannot exceed total_places"

        if errors:
            raise ValidationError(errors)

    @property
    def allocated_places(self) -> int:
        return self.total_places - self.remaining_places


class DepartmentQuota(TimeStampedModel):
    agreement_quota = models.ForeignKey(
        AgreementQuota,
        on_delete=models.CASCADE,
        related_name="department_quotas",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="agreement_quotas",
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        related_name="department_quotas",
        null=True,
        blank=True,
    )
    places = models.IntegerField(default=0)
    estimated_places = models.IntegerField(null=True, blank=True)
    is_estimated = models.BooleanField(default=False)
    is_validated = models.BooleanField(default=False)
    validated_by = models.CharField(max_length=255, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    estimation_basis = models.TextField(blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Department Quota"
        verbose_name_plural = "Department Quotas"
        ordering = ["department"]
        unique_together = ["agreement_quota", "department"]
        indexes = [
            models.Index(fields=["agreement_quota", "department"]),
        ]

    def __str__(self) -> str:
        return f"{self.department.code}: {self.places}"

    def clean(self) -> None:
        if self.places < 0:
            raise ValidationError({"places": "places cannot be negative"})
