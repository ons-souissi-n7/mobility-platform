import json

import pytest
from django.test import Client

from app.institutions.models import PartnerUniversity
from app.reference.models import Country, CTIRegion


@pytest.mark.django_db
class TestPartnerUniversityAPI:
    def setup_method(self):
        self.client = Client()
        self.country = Country.objects.create(
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
            country=self.country,
        )
        PartnerUniversity.objects.create(
            moveon_id=456,
            name="Universitat Politecnica de Catalunya",
            short_name="UPC",
            erasmus_code="E BARCELO03",
            city="Barcelona",
            country=self.country,
        )

    def test_list_universities(self):
        response = self.client.get("/api/v1/institutions/universities/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Universidad Politecnica de Madrid"
        assert data[0]["country_id"] is not None

    def test_create_university(self):
        payload = {
            "moveon_id": 789,
            "name": "Universitat de Valencia",
            "short_name": "UV",
            "translated_name": "University of Valencia",
            "erasmus_code": "E VALENCI01",
            "city": "Valencia",
            "url": "https://www.uv.es",
            "email": "international@uv.es",
            "country_id": self.country.id,
            "last_sync_moveon": None,
        }

        response = self.client.post(
            "/api/v1/institutions/universities/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Universitat de Valencia"
        assert data["country_id"] == self.country.id

    def test_update_university(self):
        university = PartnerUniversity.objects.get(moveon_id=123)
        payload = {
            "moveon_id": 123,
            "name": "Universidad Politecnica de Madrid",
            "short_name": "UPM",
            "translated_name": "Technical University of Madrid",
            "erasmus_code": "E MADRID05",
            "city": "Madrid",
            "url": "https://www.upm.es",
            "email": "international@upm.es",
            "country_id": self.country.id,
            "last_sync_moveon": None,
        }

        response = self.client.put(
            f"/api/v1/institutions/universities/{university.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["translated_name"] == "Technical University of Madrid"
        assert data["url"] == "https://www.upm.es"

    def test_create_university_invalid_country_returns_400(self):
        payload = {
            "moveon_id": 789,
            "name": "Universitat de Valencia",
            "country_id": 999,
        }

        response = self.client.post(
            "/api/v1/institutions/universities/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_delete_university(self):
        university = PartnerUniversity.objects.get(moveon_id=456)

        response = self.client.delete(
            f"/api/v1/institutions/universities/{university.id}/"
        )

        assert response.status_code == 204
        assert not PartnerUniversity.objects.filter(pk=university.id).exists()
