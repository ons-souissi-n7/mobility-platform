from django.contrib import admin

from app.reference.models import Level

from .models import (
    Agreement,
    AgreementDepartmentConstraint,
    AgreementLevelConstraint,
    AgreementQuota,
    AgreementYearAvailability,
    DepartmentQuota,
    MobilityCategory,
    RawImport,
)


@admin.register(MobilityCategory)
class MobilityCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "moveon_framework_id", "relation_types", "is_active")
    search_fields = ("name", "moveon_framework_id", "relation_types")
    list_filter = ("is_active",)


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ("name", "partner_university", "framework", "status")
    search_fields = (
        "name",
        "moveon_relation_id",
        "framework",
        "partner_university__name",
    )
    list_filter = ("status", "framework_ref")


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_active",)


@admin.register(AgreementYearAvailability)
class AgreementYearAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("agreement", "academic_year_label", "is_available", "source")
    search_fields = ("agreement__name", "academic_year_label", "remarks")
    list_filter = ("academic_year_label", "is_available", "source")


@admin.register(AgreementDepartmentConstraint)
class AgreementDepartmentConstraintAdmin(admin.ModelAdmin):
    list_display = ("agreement", "department", "is_active", "source")
    search_fields = (
        "agreement__name",
        "department__code",
        "department__name",
        "remarks",
    )
    list_filter = ("department", "is_active", "source")


@admin.register(AgreementLevelConstraint)
class AgreementLevelConstraintAdmin(admin.ModelAdmin):
    list_display = ("agreement", "level", "is_active", "source")
    search_fields = ("agreement__name", "level__code", "level__name", "remarks")
    list_filter = ("level", "is_active", "source")


@admin.register(AgreementQuota)
class AgreementQuotaAdmin(admin.ModelAdmin):
    list_display = (
        "agreement",
        "academic_year_label",
        "period",
        "total_places",
        "is_estimated",
    )
    search_fields = ("agreement__name", "academic_year_label", "period")
    list_filter = ("academic_year_label", "is_estimated", "source_scope")


@admin.register(DepartmentQuota)
class DepartmentQuotaAdmin(admin.ModelAdmin):
    list_display = ("agreement_quota", "department", "places", "is_estimated")
    list_filter = ("department", "is_estimated")


@admin.register(RawImport)
class RawImportAdmin(admin.ModelAdmin):
    list_display = ("source", "entity", "external_id", "status", "created_at")
    search_fields = ("source", "external_id", "error_message")
    list_filter = ("entity", "status")
