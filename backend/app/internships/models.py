from __future__ import annotations

from django.db import models

from app.core.models import TimeStampedModel


class Internship(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="internships",
        verbose_name="Étudiant",
    )
    academic_year = models.ForeignKey(
        "academic.AcademicYear",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="internships",
        verbose_name="Année universitaire",
    )
    company_name = models.CharField(max_length=255, verbose_name="Raison sociale")
    country = models.ForeignKey(
        "reference.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="internships",
        verbose_name="Pays",
    )
    city = models.CharField(max_length=255, blank=True, verbose_name="Ville")
    title = models.CharField(max_length=500, blank=True, verbose_name="Titre")
    internship_type = models.CharField(
        max_length=50, blank=True, verbose_name="Type de stage"
    )
    status_code = models.CharField(
        max_length=20, blank=True, verbose_name="Code statut"
    )
    status_label = models.CharField(
        max_length=255, blank=True, verbose_name="Libellé statut"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    weeks_in_company = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Nb semaines entreprise"
    )
    school_tutor = models.CharField(
        max_length=255, blank=True, verbose_name="Tuteur pédagogique"
    )
    company_tutor = models.CharField(
        max_length=255, blank=True, verbose_name="Tuteur technique entreprise"
    )
    eudonet_label = models.CharField(
        max_length=500, blank=True, verbose_name="Libellé Eudonet"
    )
    last_sync_eudonet = models.DateTimeField(
        null=True, blank=True, verbose_name="Dernière sync Eudonet"
    )

    class Meta:
        verbose_name = "Stage"
        verbose_name_plural = "Stages"
        ordering = ["-start_date", "student__last_name"]
        unique_together = [["student", "company_name", "start_date"]]
        indexes = [
            models.Index(fields=["student"], name="internship_student_idx"),
            models.Index(fields=["academic_year"], name="internship_year_idx"),
            models.Index(fields=["country"], name="internship_country_idx"),
            models.Index(fields=["start_date"], name="internship_start_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.student} — {self.company_name} ({self.start_date})"
