import json

import pytest
from django.test import Client

from app.reference.models import (
    Country,
    CTIRegion,
    Department,
    DepartmentRawImport,
    DepartmentRawImportStatus,
)


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

    def test_create_country(self):
        payload = {
            "iso2": "de",
            "name_fr": "Allemagne",
            "name_en": "Germany",
            "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
        }

        response = self.client.post(
            "/api/v1/reference/countries/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["iso2"] == "DE"
        assert Country.objects.filter(iso2="DE").exists()

    def test_update_country(self):
        country = Country.objects.get(iso2="SN")
        payload = {
            "iso2": "SN",
            "name_fr": "Senegal",
            "name_en": "Senegal",
            "cti_region": CTIRegion.AFRIQUE,
        }

        response = self.client.put(
            f"/api/v1/reference/countries/{country.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name_fr"] == "Senegal"

    def test_create_country_invalid_iso_returns_400(self):
        payload = {
            "iso2": "FRA",
            "name_fr": "France",
            "name_en": "France",
            "cti_region": CTIRegion.FRANCE,
        }

        response = self.client.post(
            "/api/v1/reference/countries/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_delete_country(self):
        country = Country.objects.get(iso2="SN")

        response = self.client.delete(f"/api/v1/reference/countries/{country.id}/")

        assert response.status_code == 204
        assert not Country.objects.filter(pk=country.id).exists()


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

    def test_create_department(self):
        payload = {"code": "3EA", "name": "Electronique Energie Electrique Automatique"}

        response = self.client.post(
            "/api/v1/reference/departments/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "3EA"
        assert Department.objects.filter(code="3EA").exists()

    def test_update_department(self):
        department = Department.objects.get(code="SN")
        payload = {"code": "SN", "name": "Sciences du numerique"}

        response = self.client.put(
            f"/api/v1/reference/departments/{department.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Sciences du numerique"

    def test_delete_department(self):
        department = Department.objects.get(code="SN")

        response = self.client.delete(f"/api/v1/reference/departments/{department.id}/")

        assert response.status_code == 204
        assert not Department.objects.filter(pk=department.id).exists()

    def test_list_department_import_errors(self):
        DepartmentRawImport.objects.create(
            source="pegase_fake_departments",
            external_id="101",
            payload={"pegase_id": 101, "code": "SN", "name": "Sciences du Numerique"},
            status=DepartmentRawImportStatus.FAILED,
            error_message="Missing department name",
        )
        DepartmentRawImport.objects.create(
            source="pegase_fake_departments",
            external_id="101",
            payload={"pegase_id": 101, "code": "SN", "name": "Sciences du Numerique"},
            status=DepartmentRawImportStatus.FAILED,
            error_message="Missing department name",
        )
        DepartmentRawImport.objects.create(
            source="pegase_fake_departments",
            external_id="102",
            payload={"pegase_id": 102, "code": "3EA", "name": "Electronique"},
            status=DepartmentRawImportStatus.IMPORTED,
        )

        response = self.client.get("/api/v1/reference/departments/import-errors/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["external_id"] == "101"

    def test_retry_department_import(self):
        raw_import = DepartmentRawImport.objects.create(
            source="pegase_fake_departments",
            external_id="105",
            payload={"pegase_id": 105, "code": "", "name": "Departement Test"},
            status=DepartmentRawImportStatus.FAILED,
            error_message="Missing department code",
        )

        response = self.client.put(
            f"/api/v1/reference/departments/import-errors/{raw_import.id}/retry/",
            data=json.dumps({"code": "TEST"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == DepartmentRawImportStatus.IMPORTED
        assert Department.objects.filter(code="TEST", pegase_id="105").exists()
