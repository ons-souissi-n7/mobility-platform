from django.core.exceptions import ValidationError
from django.db import models

from app.academic.models import AcademicYear
from app.core.models import TimeStampedModel
from app.reference.models import Department, Level, Parcours


class GenderChoice(models.TextChoices):
    MALE = "M", "Homme"
    FEMALE = "F", "Femme"


class Student(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    ine = models.CharField(max_length=11, unique=True, verbose_name="INE")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    gender = models.CharField(
        max_length=1,
        choices=GenderChoice.choices,
        blank=True,
        default="",
        verbose_name="Genre",
    )

    class Meta:
        verbose_name = "Etudiant"
        verbose_name_plural = "Etudiants"
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.last_name.upper()} {self.first_name} ({self.ine})"


class AnnualEnrollment(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    parcours = models.ForeignKey(
        Parcours,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="enrollments",
    )
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    def clean(self) -> None:
        if self.parcours_id and self.parcours.department_id != self.department_id:
            raise ValidationError(
                {
                    "parcours": "Le parcours doit appartenir au même département que l'inscription."
                }
            )

    class Meta:
        verbose_name = "Inscription annuelle"
        verbose_name_plural = "Inscriptions annuelles"
        unique_together = [("student", "academic_year")]
        ordering = ["-academic_year__start_date", "student__last_name"]

    def __str__(self) -> str:
        return f"{self.student} — {self.academic_year} ({self.level})"
