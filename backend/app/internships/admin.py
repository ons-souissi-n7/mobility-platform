from __future__ import annotations

from django.contrib import admin

from .models import Internship


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "company_name",
        "country",
        "city",
        "internship_type",
        "start_date",
        "end_date",
        "academic_year",
        "status_code",
    )
    list_filter = ("academic_year", "country", "internship_type", "status_code")
    search_fields = (
        "student__ine",
        "student__last_name",
        "student__first_name",
        "company_name",
        "city",
        "title",
    )
    raw_id_fields = ("student",)
    readonly_fields = ("created_at", "updated_at", "last_sync_eudonet")
    date_hierarchy = "start_date"
