import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from app.reference.models import Country, CTIRegion, Department


@pytest.mark.django_db
class TestCountry:
    def test_create_country(self):
        country = Country.objects.create(
            iso2="FR",
            name_fr="France",
            name_en="France",
            cti_region=CTIRegion.FRANCE,
        )

        assert country.pk is not None
        assert str(country) == "France (FR)"

    def test_iso2_unique(self):
        Country.objects.create(
            iso2="DE",
            name_fr="Allemagne",
            name_en="Germany",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )

        with pytest.raises(IntegrityError):
            Country.objects.create(
                iso2="DE",
                name_fr="Deutschland",
                name_en="Germany2",
            )

    def test_iso2_uppercase_on_clean(self):
        country = Country(iso2="fr", name_fr="France", name_en="France")

        country.clean()

        assert country.iso2 == "FR"

    def test_iso2_invalid_length_raises(self):
        country = Country(iso2="FRA", name_fr="France", name_en="France")

        with pytest.raises(ValidationError):
            country.clean()

    def test_iso2_non_alpha_raises(self):
        country = Country(iso2="F1", name_fr="France", name_en="France")

        with pytest.raises(ValidationError):
            country.clean()

    def test_cti_region_choices_match_reference_data(self):
        assert CTIRegion.values == [
            "france",
            "europe_hors_france",
            "canada_usa",
            "amerique",
            "asie_moyen_orient",
            "afrique",
            "oceanie",
        ]


@pytest.mark.django_db
class TestDepartment:
    def test_create_department(self):
        department = Department.objects.create(
            code="SN",
            name="Sciences du Numerique",
        )

        assert str(department) == "SN - Sciences du Numerique"

    def test_code_unique(self):
        Department.objects.create(code="SN", name="Sciences du Numerique")

        with pytest.raises(IntegrityError):
            Department.objects.create(code="SN", name="Doublon")

