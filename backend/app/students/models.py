from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from app.academic.models import AcademicYear
from app.core.encrypted_fields import PgEncryptedTextField
from app.core.models import TimeStampedModel
from app.reference.models import Department, Level, Parcours


class GenderChoice(models.TextChoices):
    MALE = "M", "Homme"
    FEMALE = "F", "Femme"


class Student(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    ine = models.CharField(max_length=11, unique=True, verbose_name="INE")
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
        verbose_name="Compte utilisateur",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = PgEncryptedTextField(blank=True)
    gender = models.CharField(
        max_length=1,
        choices=GenderChoice.choices,
        blank=True,
        default="",
        verbose_name="Genre",
    )
    nationality = models.ForeignKey(
        "reference.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="Nationalité",
    )
    pegase_id = PgEncryptedTextField(
        null=True,
        blank=True,
        verbose_name="Identifiant Pégase",
    )
    last_sync_pegase = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière sync Pégase",
    )

    class Meta:
        verbose_name = "Etudiant"
        verbose_name_plural = "Etudiants"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"], name="student_name_idx"),
            models.Index(fields=["last_name"], name="student_last_name_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.last_name.upper()} {self.first_name} ({self.ine})"

    def anonymize(self) -> None:
        """RGPD Art. 17 — efface les données nominatives, conserve les données statistiques."""
        self.first_name = "Anonymisé"
        self.last_name = f"ETUDIANT-{self.pk}"
        self.email = ""
        self.gender = ""
        self.nationality = None
        self.pegase_id = None
        self.last_sync_pegase = None
        self.save(
            update_fields=[
                "first_name",
                "last_name",
                "email",
                "gender",
                "nationality",
                "pegase_id",
                "last_sync_pegase",
                "updated_at",
            ]
        )


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
    is_alternant = models.BooleanField(
        default=False,
        verbose_name="Alternant (FISA)",
        help_text="Vrai pour les étudiants en apprentissage (FISA). "
        "Les FISA choisissent leur mobilité en 3ème année.",
    )
    is_scholarship = models.BooleanField(
        default=False,
        verbose_name="Boursier",
    )
    last_sync_pegase = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière sync Pégase",
    )

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
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year"],
                name="unique_enrollment_student_year",
            )
        ]
        ordering = ["-academic_year__start_date", "student__last_name"]
        indexes = [
            models.Index(fields=["academic_year"], name="students_enroll_year_idx"),
            models.Index(
                fields=["academic_year", "student"], name="students_enroll_year_stu_idx"
            ),
            models.Index(
                fields=["academic_year", "department"],
                name="students_enroll_year_dept_idx",
            ),
            models.Index(
                fields=["academic_year", "level"], name="students_enroll_year_level_idx"
            ),
            models.Index(
                fields=["academic_year", "parcours"], name="enroll_year_parcours_idx"
            ),
            models.Index(
                fields=["academic_year", "is_alternant"],
                name="enroll_year_alternant_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.student} — {self.academic_year} ({self.level})"


MAX_WISHES_PER_STUDENT = 3


class StudentWish(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    annual_enrollment = models.ForeignKey(
        AnnualEnrollment,
        on_delete=models.CASCADE,
        related_name="wishes",
    )
    agreement_year = models.ForeignKey(
        "mobility.AgreementYear",
        on_delete=models.PROTECT,
        related_name="student_wishes",
    )
    rank = models.PositiveSmallIntegerField(verbose_name="Rang du vœu")
    last_sync_moveon = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière sync MoveOn",
    )

    class Meta:
        verbose_name = "Vœu étudiant"
        verbose_name_plural = "Vœux étudiants"
        ordering = [
            "annual_enrollment__student__last_name",
            "annual_enrollment__academic_year__start_date",
            "rank",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["annual_enrollment", "rank"],
                name="unique_wish_enrollment_rank",
            ),
            models.UniqueConstraint(
                fields=["annual_enrollment", "agreement_year"],
                name="unique_wish_enrollment_agreement_year",
            ),
        ]
        indexes = [
            models.Index(fields=["annual_enrollment"], name="wish_enrollment_idx"),
            models.Index(fields=["agreement_year"], name="wish_agreement_year_idx"),
        ]

    def clean(self) -> None:
        if self.rank < 1:
            raise ValidationError({"rank": "Le rang doit être supérieur ou égal à 1."})
        if self.rank > MAX_WISHES_PER_STUDENT:
            raise ValidationError(
                {
                    "rank": f"Le rang ne peut pas dépasser {MAX_WISHES_PER_STUDENT} (maximum {MAX_WISHES_PER_STUDENT} vœux par étudiant)."
                }
            )
        existing = StudentWish.objects.filter(annual_enrollment=self.annual_enrollment)
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.count() >= MAX_WISHES_PER_STUDENT:
            raise ValidationError(
                f"Un étudiant ne peut pas avoir plus de {MAX_WISHES_PER_STUDENT} vœux."
            )

    def __str__(self) -> str:
        return f"{self.annual_enrollment.student} — Vœu {self.rank} ({self.annual_enrollment.academic_year})"
