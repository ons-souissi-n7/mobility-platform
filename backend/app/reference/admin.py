from django.contrib import admin

from .models import Country, Department


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["iso2", "name_fr", "cti_region"]
    list_filter = ["cti_region"]
    search_fields = ["iso2", "name_fr", "name_en"]
    ordering = ["name_fr"]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]
