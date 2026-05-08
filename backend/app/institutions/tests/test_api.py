import pytest
from django.test import Client

from app.institutions.models import PartnerUniversity
from app.reference.models import Country, CTIRegion


@pytest.mark.django_db
class TestPartnerUniversityAPI:
    def setup_method(self):
        self.client = Client()
        country = Country.objects.create(
            iso2="ES",
            name_fr="Espagne",
            name_en="Spain",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )
        PartnerUniversity.objects.create(
            moveon_id=123,
            name="Universidad Politecnica de Madrid",
            short_name="UPM",
            erasmus_code="E MADRID05",
            city="Madrid",
            country=country,
        )
        PartnerUniversity.objects.create(
            moveon_id=456,
            name="Universitat Politecnica de Catalunya",
            short_name="UPC",
            erasmus_code="E BARCELO03",
            city="Barcelona",
            country=country,
        )

    def test_list_universities(self):
        response = self.client.get("/api/v1/institutions/universities/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Universidad Politecnica de Madrid"
        assert data[0]["country_id"] is not None
