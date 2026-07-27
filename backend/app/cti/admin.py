from django.contrib import admin

from app.cti.models import MobilityDuration


@admin.register(MobilityDuration)
class MobilityDurationAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exchange_weeks",
        "internship_weeks",
        "complementary_weeks",
        "total_weeks",
        "updated_at",
    )
    search_fields = ("student__ine", "student__last_name", "student__first_name")
    readonly_fields = (
        "exchange_weeks",
        "internship_weeks",
        "complementary_weeks",
        "total_weeks",
        "created_at",
        "updated_at",
    )
    ordering = ("-total_weeks",)
