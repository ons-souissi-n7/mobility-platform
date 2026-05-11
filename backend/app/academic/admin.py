from django.contrib import admin

from .models import AcademicYear


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = [
        "label",
        "start_date",
        "end_date",
        "status",
        "wishes_open_date",
        "wishes_close_date",
    ]
    list_filter = ["status"]
    search_fields = ["label"]
    ordering = ["-start_date"]
    readonly_fields = ["created_at", "updated_at"]
