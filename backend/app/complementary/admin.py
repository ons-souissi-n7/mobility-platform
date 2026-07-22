from django.contrib import admin

from .models import ComplementaryMobility


@admin.register(ComplementaryMobility)
class ComplementaryMobilityAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "experience_type",
        "destination_country",
        "destination_institution",
        "start_date",
        "end_date",
        "academic_year",
        "status",
    )
    list_filter = ("academic_year", "status", "destination_country")
    search_fields = (
        "student__ine",
        "student__last_name",
        "student__first_name",
        "experience_type",
        "destination_institution",
    )
    raw_id_fields = ("student",)
    readonly_fields = ("created_at", "updated_at", "rejection_reason")
    date_hierarchy = "start_date"
