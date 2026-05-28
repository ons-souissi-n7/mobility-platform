from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.audit"

    def ready(self) -> None:
        from auditlog.registry import auditlog

        from app.academic.models import AcademicYear
        from app.mobility.models import Agreement, AgreementQuota

        auditlog.register(AcademicYear)
        auditlog.register(Agreement)
        auditlog.register(AgreementQuota)
