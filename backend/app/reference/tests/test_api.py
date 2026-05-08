import pytest
from django.test import Client

from app.reference.models import Country, CTIRegion, Department


@pytest.mark.django_db
class TestCountryAPI:
    def setup_method(self):
        self.client = Client()
        Country.objects.create(
            iso2="FR",
            name_fr="France",
            name_en="France",
            cti_region=CTIRegion.FRANCE,
        )
        Country.objects.create(
            iso2="SN",
            name_fr="Sénégal",
            name_en="Senegal",
            cti_region=CTIRegion.AFRIQUE,
        )

    def test_list_countries(self):
        response = self.client.get("/api/v1/reference/countries/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["iso2"] == "FR"


@pytest.mark.django_db
class TestDepartmentAPI:
    def setup_method(self):
        self.client = Client()
        Department.objects.create(code="SN", name="Sciences du Numerique")
        Department.objects.create(
            code="MF2E", name="Mécanique des Fluides, Énergétique & Environnement"
        )

    def test_list_departments(self):
        response = self.client.get("/api/v1/reference/departments/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["code"] == "MF2E"
