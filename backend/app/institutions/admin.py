from django.contrib import admin

from .models import PartnerUniversity


@admin.register(PartnerUniversity)
class PartnerUniversityAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "city", "erasmus_code", "moveon_id"]
    list_filter = ["country"]
    search_fields = [
        "name",
        "short_name",
        "translated_name",
        "erasmus_code",
        "city",
        "country__iso2",
        "country__name_fr",
        "country__name_en",
    ]
    ordering = ["name"]
