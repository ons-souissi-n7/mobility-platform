from django.core.exceptions import ValidationError
from django.db import models

from app.academic.models import AcademicYear
from app.core.models import TimeStampedModel
from app.institutions.models import PartnerUniversity
from app.reference.models import Department, Level


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
    duration_weeks = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Durée (semaines)",
        help_text=(
            "Durée standard du séjour, reprise comme valeur par défaut pour "
            "chaque nouvelle instance annuelle de cet accord (modifiable "
            "ensuite instance par instance)."
        ),
    )
    remarks = models.TextField(blank=True)
    last_sync_moveon = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Supprimé le",
        help_text=(
            "Suppression douce : l'accord n'est plus actif à partir de maintenant "
            "(plus d'instance future) mais son historique dans les années déjà "
            "closes reste intact."
        ),
    )
    levels = models.ManyToManyField(
        Level,
        blank=True,
        related_name="agreements",
    )

    class Meta:
        verbose_name = "Agreement"
        verbose_name_plural = "Agreements"
        # "id" en dernier critère : name n'est pas unique, donc sans tiebreaker
        # la pagination LIMIT/OFFSET n'est pas garantie stable entre requêtes.
        ordering = ["name", "id"]
        indexes = [
            models.Index(fields=["partner_university"]),
            models.Index(fields=["name"], name="agreement_name_idx"),
            models.Index(
                fields=["partner_university", "name"], name="agreement_univ_name_idx"
            ),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.partner_university.name}"

    def clean(self) -> None:
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValidationError(
                {"valid_until": "valid_from doit être avant valid_until"}
            )

    @property
    def level_ids(self) -> list[int]:
        return [lvl.id for lvl in self.levels.all()]

    def is_valid_for_year(self, year: "AcademicYear") -> bool:
        """Retourne False si l'accord est expiré par rapport à l'année donnée."""
        if self.valid_from and year.end_date and self.valid_from > year.end_date:
            return False
        if self.valid_until and year.start_date and self.valid_until < year.start_date:
            return False
        return True

    def is_eligible(self, dept_id: int) -> bool:
        """Retourne True si le département est autorisé pour cet accord."""
        return self.agreement_departments.filter(department_id=dept_id).exists()


class AgreementDepartment(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    agreement = models.ForeignKey(
        Agreement,
        on_delete=models.CASCADE,
        related_name="agreement_departments",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="agreement_departments",
    )
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Agreement Department"
        verbose_name_plural = "Agreement Departments"
        ordering = ["department__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "department"],
                name="unique_agreement_department",
            ),
        ]
        indexes = [
            models.Index(fields=["agreement", "department"]),
        ]

    def __str__(self) -> str:
        return f"{self.agreement.name} — {self.department.code}"

    @property
    def department_id_val(self) -> int:
        return self.department_id


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
    inp_total_places = models.IntegerField(default=0)
    n7_places = models.IntegerField(default=0)
    is_validated = models.BooleanField(default=False)
    validated_by = models.CharField(max_length=255, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    duration_weeks = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Durée (semaines)",
        help_text="Durée standard du séjour en semaines, utilisée pour le calcul CTI.",
    )

    class Meta:
        verbose_name = "Agreement Year"
        verbose_name_plural = "Agreement Years"
        # "id" en dernier critère : sans clé de tri unique, LIMIT/OFFSET n'est
        # pas garanti stable entre deux requêtes (les égalités de tri peuvent
        # être ordonnées différemment), ce qui peut faire apparaître une même
        # ligne sur deux pages consécutives lors d'une pagination complète.
        ordering = ["-academic_year__label", "agreement__name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "academic_year"],
                name="unique_agreement_year",
            ),
        ]
        indexes = [
            models.Index(fields=["academic_year"], name="mobility_agrmt_year_idx"),
            models.Index(fields=["agreement", "academic_year"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        status = "actif" if self.is_active else "inactif"
        return f"{self.agreement.name} – {self.academic_year.label} ({status})"

    def clean(self) -> None:
        if self.n7_places < 0:
            raise ValidationError({"n7_places": "n7_places ne peut pas être négatif"})
        if self.inp_total_places < 0:
            raise ValidationError(
                {"inp_total_places": "inp_total_places ne peut pas être négatif"}
            )
        effective_inp = self.inp_total_places or (
            self.agreement.inp_total_places if self.agreement_id else 0
        )
        if effective_inp > 0 and self.n7_places > effective_inp:
            raise ValidationError(
                {
                    "n7_places": "Le quota N7 ne peut pas dépasser le quota INP de l'accord."
                }
            )

    @property
    def academic_year_label(self) -> str:
        return self.academic_year.label


class NomenclatureMapping(TimeStampedModel):
    """
    Clé sémantique externe → Accord interne.

    Générée automatiquement lors du sync MoveON et éditée manuellement pour les
    accords créés sans synchronisation (ex: accord Eudonet saisi à la main).

    La résolution des vœux MoveON utilise cette table en dernier recours :
    si l'accord n'est pas trouvé par moveon_id ni par nom, on cherche ici via
    moveon_offer_name (le texte exact de l'« Offre de séjour » MoveON).
    """

    partner_university = models.ForeignKey(
        PartnerUniversity,
        on_delete=models.CASCADE,
        related_name="nomenclature_mappings",
        verbose_name="Université partenaire",
    )
    category = models.ForeignKey(
        MobilityCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nomenclature_mappings",
        verbose_name="Cadre de mobilité",
    )
    date_debut = models.DateField(null=True, blank=True, verbose_name="Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    moveon_offer_name = models.CharField(
        max_length=500,
        verbose_name="Nom de l'offre MoveON",
        help_text="Texte exact reçu dans le champ « Offre de séjour » lors du sync des vœux.",
    )
    agreement = models.OneToOneField(
        Agreement,
        on_delete=models.CASCADE,
        related_name="nomenclature",
        verbose_name="Accord",
    )

    class Meta:
        verbose_name = "Nomenclature accord"
        verbose_name_plural = "Nomenclature accords"
        ordering = ["partner_university__name", "date_debut"]
        indexes = [
            models.Index(
                fields=["moveon_offer_name"], name="nomenclature_offer_name_idx"
            ),
            models.Index(
                fields=["partner_university", "category"],
                name="nomenclature_univ_cat_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.moveon_offer_name} → {self.agreement.name}"


class AgreementYearDepartment(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    agreement_year = models.ForeignKey(
        AgreementYear,
        on_delete=models.CASCADE,
        related_name="department_quotas",
    )
    agreement_department = models.ForeignKey(
        AgreementDepartment,
        on_delete=models.PROTECT,
        related_name="year_quotas",
    )
    estimated_places = models.IntegerField(default=0)
    adjusted_places = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Quota ajusté N7",
        help_text="Remplace le quota estimé quand renseigné manuellement.",
    )

    class Meta:
        verbose_name = "Agreement Year Department"
        verbose_name_plural = "Agreement Year Departments"
        # "id" en dernier critère : seulement 3 codes départements pour des
        # centaines de lignes, donc énormément d'égalités de tri — sans
        # tiebreaker unique, la pagination LIMIT/OFFSET peut renvoyer la même
        # ligne sur deux pages consécutives (clé React dupliquée observée).
        ordering = ["agreement_department__department__code", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["agreement_year", "agreement_department"],
                name="unique_agreement_year_department",
            ),
        ]
        indexes = [
            models.Index(fields=["agreement_year", "agreement_department"]),
        ]

    def __str__(self) -> str:
        return f"{self.agreement_department.department.code}: {self.estimated_places}"

    def clean(self) -> None:
        if self.estimated_places < 0:
            raise ValidationError(
                {"estimated_places": "estimated_places ne peut pas être négatif"}
            )
        if self.adjusted_places is not None and self.adjusted_places < 0:
            raise ValidationError(
                {"adjusted_places": "adjusted_places ne peut pas être négatif"}
            )
        if (
            self.agreement_department_id
            and self.agreement_year_id
            and self.agreement_department.agreement_id
            != self.agreement_year.agreement_id
        ):
            raise ValidationError(
                {
                    "agreement_department": "Ce département n'appartient pas à cet accord."
                }
            )

    def get_effective_quota(self) -> int:
        """Retourne le quota ajusté s'il est renseigné, sinon le quota estimé."""
        if self.adjusted_places is not None:
            return self.adjusted_places
        return self.estimated_places

    @property
    def department_id(self) -> int:
        return self.agreement_department.department_id
