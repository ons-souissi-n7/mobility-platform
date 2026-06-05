from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.audit"

    def ready(self) -> None:
        from auditlog.registry import auditlog

        # -- Référentiels -------------------------------------------------------
        from app.reference.models import Country, Department, Level, Parcours

        auditlog.register(Country)
        auditlog.register(Department)
        auditlog.register(Level)
        auditlog.register(Parcours)

        # -- Institutions -------------------------------------------------------
        from app.institutions.models import PartnerUniversity

        auditlog.register(PartnerUniversity)

        # -- Années universitaires ----------------------------------------------
        from app.academic.models import AcademicYear

        auditlog.register(AcademicYear)

        # -- Mobilité (accords, quotas, catégories) ----------------------------
        from app.mobility.models import (
            Agreement,
            AgreementYear,
            AgreementYearDepartment,
            MobilityCategory,
        )

        auditlog.register(MobilityCategory)
        auditlog.register(Agreement)
        auditlog.register(AgreementYear)
        auditlog.register(AgreementYearDepartment)

        # -- Imports (rapports de run + erreurs brutes) ------------------------
        from app.imports.models import ImportReport, RawImport

        auditlog.register(ImportReport)
        auditlog.register(RawImport)

        # -- Étudiants ----------------------------------------------------------
        from app.students.models import AnnualEnrollment, Student

        auditlog.register(Student)
        auditlog.register(AnnualEnrollment)
