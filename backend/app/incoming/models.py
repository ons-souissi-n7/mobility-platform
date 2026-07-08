from __future__ import annotations

from django.db import models

from app.core.models import TimeStampedModel


class IncomingStudent(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    academic_year = models.ForeignKey(
        "academic.AcademicYear",
        on_delete=models.PROTECT,
        related_name="incoming_students",
        verbose_name="Année universitaire",
    )
    department = models.ForeignKey(
        "reference.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_students",
        verbose_name="Département N7",
    )
    civility = models.CharField(max_length=10, blank=True, verbose_name="Civilité")
    last_name = models.CharField(max_length=255, verbose_name="Nom")
    first_name = models.CharField(max_length=255, verbose_name="Prénom")
    country = models.ForeignKey(
        "reference.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_students",
        verbose_name="Pays",
    )
    origin_university = models.ForeignKey(
        "institutions.PartnerUniversity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_students",
        verbose_name="Université d'origine (liée)",
    )
    origin_university_name = models.CharField(
        max_length=500, blank=True, verbose_name="Université d'origine"
    )
    birth_date = models.DateField(
        null=True, blank=True, verbose_name="Date de naissance"
    )
    mobility_category = models.ForeignKey(
        "mobility.MobilityCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_students",
        verbose_name="Cadre de mobilité",
    )
    personal_email = models.EmailField(blank=True, verbose_name="Email personnel")
    n7_email = models.EmailField(blank=True, verbose_name="Email ENSEEIHT")
    duration = models.CharField(max_length=100, blank=True, verbose_name="Durée")
    level = models.ForeignKey(
        "reference.Level",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_students",
        verbose_name="Niveau / Année",
    )
    parcours = models.ForeignKey(
        "reference.Parcours",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_students",
        verbose_name="Parcours",
    )
    remarks = models.TextField(blank=True, verbose_name="Remarques")
    internship_info = models.TextField(blank=True, verbose_name="Stage")
    diploma_info = models.TextField(blank=True, verbose_name="Diplôme")
    doctoral_continuation = models.BooleanField(
        default=False, verbose_name="Poursuite doctorat"
    )

    class Meta:
        verbose_name = "Étudiant entrant"
        verbose_name_plural = "Étudiants entrants"
        ordering = ["-academic_year__start_date", "last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "last_name", "first_name", "birth_date"],
                name="unique_incoming_year_name_birthdate",
            )
        ]
        indexes = [
            models.Index(fields=["academic_year"], name="incoming_year_idx"),
            models.Index(fields=["country"], name="incoming_country_idx"),
            models.Index(fields=["department"], name="incoming_dept_idx"),
            models.Index(fields=["last_name", "first_name"], name="incoming_name_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} ({self.academic_year})"
