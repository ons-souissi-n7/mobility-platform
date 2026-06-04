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


class MobilityCategory(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    moveon_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    last_sync_moveon = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Cadre de mobilité"
        verbose_name_plural = "Cadres de mobilité"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["moveon_id"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class Agreement(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    moveon_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    reference = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255)
    partner_university = models.ForeignKey(
        PartnerUniversity,
        on_delete=models.PROTECT,
        related_name="agreements",
    )
    category = models.ForeignKey(
        MobilityCategory,
        on_delete=models.PROTECT,
        related_name="agreements",
        null=True,
        blank=True,
    )
    direction = models.CharField(max_length=50, default="unknown")
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    inp_total_places = models.IntegerField(default=0)
    inp_institutions = models.CharField(max_length=500, blank=True)
    remarks = models.TextField(blank=True)
    last_sync_moveon = models.DateTimeField(null=True, blank=True)
    levels = models.ManyToManyField(
        Level,
        blank=True,
        related_name="agreements",
    )
    departments = models.ManyToManyField(
        Department,
        blank=True,
        related_name="agreements",
    )

    class Meta:
        verbose_name = "Agreement"
        verbose_name_plural = "Agreements"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["partner_university"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.partner_university.name}"

    def clean(self) -> None:
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValidationError(
                {"valid_until": "valid_from doit être avant valid_until"}
            )

    @property
    def department_ids(self) -> list[int]:
        return [d.id for d in self.departments.all()]

    @property
    def level_ids(self) -> list[int]:
        return [lvl.id for lvl in self.levels.all()]


class AgreementYear(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="year_instances",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="agreement_years",
    )
    is_active = models.BooleanField(default=True)
    n7_places = models.IntegerField(default=0)
    is_validated = models.BooleanField(default=False)
    validated_by = models.CharField(max_length=255, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Agreement Year"
        verbose_name_plural = "Agreement Years"
        ordering = ["-academic_year__label", "agreement__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "academic_year"],
                name="unique_agreement_year",
            ),
        ]
        indexes = [
            models.Index(fields=["agreement", "academic_year"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        status = "actif" if self.is_active else "inactif"
        return f"{self.agreement.name} – {self.academic_year.label} ({status})"

    def clean(self) -> None:
        if self.n7_places < 0:
            raise ValidationError({"n7_places": "n7_places ne peut pas être négatif"})
        if self.agreement_id and self.n7_places > self.agreement.inp_total_places:
            raise ValidationError(
                {
                    "n7_places": "Le quota N7 ne peut pas dépasser le quota INP de l'accord."
                }
            )

    @property
    def academic_year_label(self) -> str:
        return self.academic_year.label


class AgreementYearDepartment(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    agreement_year = models.ForeignKey(
        AgreementYear,
        on_delete=models.CASCADE,
        related_name="department_quotas",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="agreement_year_departments",
    )
    estimated_places = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Agreement Year Department"
        verbose_name_plural = "Agreement Year Departments"
        ordering = ["department__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement_year", "department"],
                name="unique_agreement_year_department",
            ),
        ]
        indexes = [
            models.Index(fields=["agreement_year", "department"]),
        ]

    def __str__(self) -> str:
        return f"{self.department.code}: {self.estimated_places}"

    def clean(self) -> None:
        if self.estimated_places < 0:
            raise ValidationError(
                {"estimated_places": "estimated_places ne peut pas être négatif"}
            )
        if self.department_id and self.agreement_year_id:
            constrained = list(
                self.agreement_year.agreement.departments.values_list("id", flat=True)
            )
            if constrained and self.department_id not in constrained:
                raise ValidationError(
                    {
                        "department": "Ce département n'est pas dans les contraintes de l'accord."
                    }
                )
