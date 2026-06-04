from django.contrib import admin

from app.imports.models import RawImport

from .models import (
    Agreement,
    AgreementYear,
    AgreementYearDepartment,
    MobilityCategory,
)


@admin.register(MobilityCategory)
class MobilityCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "moveon_id", "last_sync_moveon", "created_at"]
    search_fields = ["name", "moveon_id"]


class AgreementYearInline(admin.TabularInline):
    model = AgreementYear
    extra = 0
    fields = ["academic_year", "is_active", "n7_places", "is_validated", "validated_by"]
    readonly_fields = ["is_validated", "validated_by", "validated_at"]


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "partner_university",
        "category",
        "direction",
        "valid_from",
        "valid_until",
        "inp_total_places",
        "last_sync_moveon",
    ]
    list_filter = ["category", "direction"]
    search_fields = ["name", "partner_university__name", "reference"]
    filter_horizontal = ["departments", "levels"]
    readonly_fields = ["moveon_id", "last_sync_moveon", "created_at", "updated_at"]
    inlines = [AgreementYearInline]
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "reference",
                    "moveon_id",
                    "partner_university",
                    "category",
                    "direction",
                ],
            },
        ),
        (
            "Validité",
            {
                "fields": [
                    "valid_from",
                    "valid_until",
                    "inp_total_places",
                    "inp_institutions",
                ],
            },
        ),
        (
            "Contraintes",
            {
                "fields": ["levels", "departments"],
            },
        ),
        (
            "Informations",
            {
                "fields": ["remarks", "last_sync_moveon", "created_at", "updated_at"],
            },
        ),
    ]


class AgreementYearDepartmentInline(admin.TabularInline):
    model = AgreementYearDepartment
    extra = 0
    fields = ["department", "estimated_places"]


@admin.register(AgreementYear)
class AgreementYearAdmin(admin.ModelAdmin):
    list_display = [
        "agreement",
        "academic_year",
        "is_active",
        "n7_places",
        "is_validated",
        "validated_by",
        "validated_at",
    ]
    list_filter = ["is_active", "is_validated", "academic_year"]
    search_fields = ["agreement__name", "academic_year__label"]
    readonly_fields = [
        "is_validated",
        "validated_by",
        "validated_at",
        "created_at",
        "updated_at",
    ]
    inlines = [AgreementYearDepartmentInline]


@admin.register(AgreementYearDepartment)
class AgreementYearDepartmentAdmin(admin.ModelAdmin):
    list_display = ["agreement_year", "department", "estimated_places"]
    list_filter = ["department"]
    search_fields = ["agreement_year__agreement__name", "department__code"]


@admin.register(RawImport)
class RawImportAdmin(admin.ModelAdmin):
    list_display = [
        "source",
        "entity",
        "external_id",
        "status",
        "imported_at",
        "created_at",
    ]
    list_filter = ["status", "entity", "source"]
    search_fields = ["external_id", "error_message"]
    readonly_fields = ["created_at", "updated_at"]
