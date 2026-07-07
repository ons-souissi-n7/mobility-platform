from django.db import models

from app.academic.models import AcademicYear
from app.core.models import TimeStampedModel


class RawImportStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    IMPORTED = "imported", "Importé"
    FAILED = "failed", "Échoué"
    IGNORED = "ignored", "Ignoré"
    CONFLICT = "conflict", "Conflit"


class RawImportEntity(models.TextChoices):
    DEPARTMENT = "department", "Département"
    LEVEL = "level", "Niveau"
    PARTNER_UNIVERSITY = "partner_university", "Université partenaire"
    AGREEMENT_CATEGORY = "agreement_category", "Catégorie d'accord"
    AGREEMENT = "agreement", "Accord"
    STUDENT = "student", "Étudiant"
    INTERNSHIP = "internship", "Stage"


class RawImport(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    source = models.CharField(max_length=255)
    source_file = models.CharField(max_length=255, blank=True)
    external_id = models.CharField(max_length=255)
    payload = models.JSONField()
    entity = models.CharField(
        max_length=50,
        choices=RawImportEntity.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=RawImportStatus.choices,
        default=RawImportStatus.PENDING,
    )
    error_message = models.TextField(blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)
    academic_year = models.ForeignKey(
        "academic.AcademicYear",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_imports",
        verbose_name="Année universitaire",
    )
    import_report = models.ForeignKey(
        "imports.ImportReport",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_imports",
        verbose_name="Rapport d'import",
    )

    class Meta:
        verbose_name = "Import brut"
        verbose_name_plural = "Imports bruts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["entity", "external_id"], name="imports_raw_entity_extid_idx"
            ),
            models.Index(fields=["status"], name="imports_raw_status_idx"),
            models.Index(fields=["entity"], name="imports_raw_entity_idx"),
            models.Index(fields=["import_report"], name="imports_raw_report_idx"),
            models.Index(fields=["academic_year"], name="imports_raw_year_idx"),
            models.Index(
                fields=["academic_year", "status"], name="imports_raw_year_status_idx"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.entity} — {self.external_id} ({self.status})"


class ImportSource(models.TextChoices):
    MOVEON_ACCORDS = "moveon_accords", "MoveON – Accords"
    MOVEON_CATEGORIES = "moveon_categories", "MoveON – Catégories"
    MOVEON_QUOTAS = "moveon_quotas", "MoveON – Quotas"
    MOVEON_WISHES = "moveon_wishes", "MoveON – Vœux"
    PEGASE = "pegase", "Pégase – Étudiants"
    EUDONET = "eudonet", "Eudonet – Stages"
    EXCEL = "excel", "Import Excel"
    EXCEL_OVERRIDES = "excel_overrides", "Import Excel – Corrections affectation"


class ImportReport(TimeStampedModel):
    """
    Une ligne par session d'import (un run du pipeline ETL).
    Agrège les compteurs de succès/erreurs et le détail des rejets.
    """

    id = models.BigAutoField(primary_key=True)
    source = models.CharField(
        max_length=50,
        choices=ImportSource.choices,
        verbose_name="Source",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_reports",
        verbose_name="Année universitaire",
    )
    total = models.IntegerField(default=0, verbose_name="Total traités")
    success_count = models.IntegerField(default=0, verbose_name="Succès")
    error_count = models.IntegerField(default=0, verbose_name="Erreurs")
    duplicate_count = models.IntegerField(default=0, verbose_name="Doublons ignorés")
    # [{external_id: str, reason: str, raw_import_id: int|null}, ...]
    errors = models.JSONField(default=list, verbose_name="Détail des erreurs")
    triggered_by = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Déclenché par",
    )

    class Meta:
        verbose_name = "Rapport d'import"
        verbose_name_plural = "Rapports d'import"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source"], name="imports_report_source_idx"),
            models.Index(fields=["academic_year"], name="imports_report_year_idx"),
            models.Index(fields=["-created_at"], name="imports_report_date_idx"),
        ]

    def __str__(self) -> str:
        ts = self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "—"
        return f"{self.get_source_display()} — {ts} ({self.success_count}/{self.total})"

    # ── helpers appelés pendant le pipeline (pas de save intermédiaire) ────────

    def record_success(self) -> None:
        self.success_count += 1
        self.total += 1

    def record_duplicate(self, external_id: str = "") -> None:
        self.duplicate_count += 1
        self.total += 1

    def record_error(
        self, external_id: str, reason: str, raw_import_id: int | None = None
    ) -> None:
        self.error_count += 1
        self.total += 1
        entry: dict = {"external_id": external_id, "reason": reason}
        if raw_import_id is not None:
            entry["raw_import_id"] = raw_import_id
        self.errors.append(entry)

    def record_conflict(
        self, external_id: str, reason: str, raw_import_id: int | None = None
    ) -> None:
        """Record a sync conflict — locally-modified record blocked from being overwritten."""
        self.error_count += 1
        self.total += 1
        entry: dict = {
            "external_id": external_id,
            "reason": reason,
            "is_conflict": True,
        }
        if raw_import_id is not None:
            entry["raw_import_id"] = raw_import_id
        self.errors.append(entry)

    def finalize(self) -> None:
        """Persiste les compteurs finaux en base."""
        self.save(
            update_fields=[
                "total",
                "success_count",
                "error_count",
                "duplicate_count",
                "errors",
                "updated_at",
            ]
        )
