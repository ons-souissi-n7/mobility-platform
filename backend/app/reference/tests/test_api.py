import json
from unittest.mock import patch

import pytest
from django.test import Client

from app.imports.models import RawImport, RawImportEntity, RawImportStatus
from app.reference.models import (
    Country,
    CTIRegion,
    Department,
    Level,
    Parcours,
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
        RawImport.objects.create(
            source="pegase_fake_departments",
            entity=RawImportEntity.DEPARTMENT,
            external_id="101",
            payload={"pegase_id": 101, "code": "SN", "name": "Sciences du Numerique"},
            status=RawImportStatus.FAILED,
            error_message="Missing department name",
        )
        RawImport.objects.create(
            source="pegase_fake_departments",
            entity=RawImportEntity.DEPARTMENT,
            external_id="101",
            payload={"pegase_id": 101, "code": "SN", "name": "Sciences du Numerique"},
            status=RawImportStatus.FAILED,
            error_message="Missing department name",
        )
        RawImport.objects.create(
            source="pegase_fake_departments",
            entity=RawImportEntity.DEPARTMENT,
            external_id="102",
            payload={"pegase_id": 102, "code": "3EA", "name": "Electronique"},
            status=RawImportStatus.IMPORTED,
        )

        response = self.client.get("/api/v1/reference/departments/import-errors/")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["external_id"] == "101"

    def test_retry_department_import(self):
        raw_import = RawImport.objects.create(
            source="pegase_fake_departments",
            entity=RawImportEntity.DEPARTMENT,
            external_id="105",
            payload={"pegase_id": 105, "code": "", "name": "Departement Test"},
            status=RawImportStatus.FAILED,
            error_message="Missing department code",
        )

        response = self.client.put(
            f"/api/v1/reference/departments/import-errors/{raw_import.id}/retry/",
            data=json.dumps({"code": "TEST"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == RawImportStatus.IMPORTED
        assert Department.objects.filter(code="TEST", pegase_id="105").exists()

    def test_select_options(self):
        response = self.client.get("/api/v1/reference/departments/select-options/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("id" in item and "label" in item for item in data)

    def test_list_all_department_imports(self):
        RawImport.objects.create(
            source="pegase_dept",
            entity=RawImportEntity.DEPARTMENT,
            external_id="201",
            payload={"code": "SN"},
            status=RawImportStatus.IMPORTED,
        )
        RawImport.objects.create(
            source="pegase_dept",
            entity=RawImportEntity.DEPARTMENT,
            external_id="202",
            payload={"code": "TC"},
            status=RawImportStatus.FAILED,
            error_message="Missing name",
        )

        response = self.client.get("/api/v1/reference/departments/imports/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_ignore_department_import(self):
        raw = RawImport.objects.create(
            source="pegase_dept",
            entity=RawImportEntity.DEPARTMENT,
            external_id="203",
            payload={"code": "XX"},
            status=RawImportStatus.FAILED,
            error_message="Unknown dept",
        )

        response = self.client.put(
            f"/api/v1/reference/departments/import-errors/{raw.id}/ignore/"
        )

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IGNORED
        assert "Traite manuellement" in raw.error_message

    @patch("app.reference.api.enqueue_sync_pegase_departments")
    def test_sync_departments_trigger(self, mock_enqueue):
        mock_enqueue.return_value = "task-dept-001"

        response = self.client.post("/api/v1/reference/departments/sync-pegase/")

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "task-dept-001"
        mock_enqueue.assert_called_once()

    def test_update_department_not_found(self):
        response = self.client.put(
            "/api/v1/reference/departments/99999/",
            data=json.dumps({"code": "XX", "name": "Inexistant"}),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_delete_department_not_found(self):
        response = self.client.delete("/api/v1/reference/departments/99999/")

        assert response.status_code == 404

    @patch("app.reference.api.upsert_department")
    def test_force_overwrite_department_import(self, mock_upsert):
        raw = RawImport.objects.create(
            source="pegase_dept",
            entity=RawImportEntity.DEPARTMENT,
            external_id="300",
            payload={"pegase_id": "300", "code": "TC", "name": "Tronc Commun"},
            status=RawImportStatus.CONFLICT,
        )

        response = self.client.post(
            f"/api/v1/reference/departments/import-errors/{raw.id}/force-overwrite/"
        )

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IMPORTED
        mock_upsert.assert_called_once()

    def test_force_overwrite_department_not_found(self):
        response = self.client.post(
            "/api/v1/reference/departments/import-errors/99999/force-overwrite/"
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCountryExtraAPI:
    def setup_method(self):
        self.client = Client()
        self.country = Country.objects.create(
            iso2="FR", name_fr="France", name_en="France", cti_region=CTIRegion.FRANCE
        )
        Country.objects.create(
            iso2="DE",
            name_fr="Allemagne",
            name_en="Germany",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )

    def test_select_options(self):
        response = self.client.get("/api/v1/reference/countries/select-options/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("id" in item and "label" in item for item in data)

    def test_update_country_not_found(self):
        payload = {
            "iso2": "XX",
            "name_fr": "Inexistant",
            "name_en": "Nonexistent",
            "cti_region": CTIRegion.EUROPE_HORS_FRANCE,
        }

        response = self.client.put(
            "/api/v1/reference/countries/99999/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestLevelAPI:
    def setup_method(self):
        self.client = Client()
        self.level = Level.objects.create(code="3A", name="Troisième année")
        Level.objects.create(code="4A", name="Quatrième année")

    def test_list_levels(self):
        response = self.client.get("/api/v1/reference/levels/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_select_options(self):
        response = self.client.get("/api/v1/reference/levels/select-options/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("id" in item and "label" in item for item in data)

    def test_create_level(self):
        payload = {"code": "5A", "name": "Cinquième année"}

        response = self.client.post(
            "/api/v1/reference/levels/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json()["code"] == "5A"
        assert Level.objects.filter(code="5A").exists()

    @patch("app.reference.api.enqueue_sync_pegase_levels")
    def test_sync_levels_trigger(self, mock_enqueue):
        mock_enqueue.return_value = "task-levels-001"

        response = self.client.post("/api/v1/reference/levels/sync/")

        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "task-levels-001"
        mock_enqueue.assert_called_once()

    def test_list_level_import_errors(self):
        RawImport.objects.create(
            source="pegase_levels",
            entity=RawImportEntity.LEVEL,
            external_id="L1",
            payload={"code": "3A"},
            status=RawImportStatus.FAILED,
            error_message="Validation error",
        )
        RawImport.objects.create(
            source="pegase_levels",
            entity=RawImportEntity.LEVEL,
            external_id="L2",
            payload={"code": "4A"},
            status=RawImportStatus.IMPORTED,
        )

        response = self.client.get("/api/v1/reference/levels/import-errors/")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["external_id"] == "L1"

    def test_ignore_level_import(self):
        raw = RawImport.objects.create(
            source="pegase_levels",
            entity=RawImportEntity.LEVEL,
            external_id="L3",
            payload={"code": "6A"},
            status=RawImportStatus.FAILED,
            error_message="Missing label",
        )

        response = self.client.put(
            f"/api/v1/reference/levels/import-errors/{raw.id}/ignore/"
        )

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IGNORED
        assert "Traite manuellement" in raw.error_message

    @patch("app.reference.services.sync_pegase_levels._upsert_level")
    def test_force_overwrite_level_import(self, mock_upsert):
        raw = RawImport.objects.create(
            source="pegase_levels",
            entity=RawImportEntity.LEVEL,
            external_id="L4",
            payload={"code": "6A", "label": "Sixième année"},
            status=RawImportStatus.CONFLICT,
        )

        response = self.client.post(
            f"/api/v1/reference/levels/import-errors/{raw.id}/force-overwrite/"
        )

        assert response.status_code == 200
        raw.refresh_from_db()
        assert raw.status == RawImportStatus.IMPORTED
        mock_upsert.assert_called_once_with(raw.payload, force_overwrite=True)

    def test_update_level(self):
        payload = {"code": "3A", "name": "Troisième année (modifié)"}

        response = self.client.put(
            f"/api/v1/reference/levels/{self.level.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Troisième année (modifié)"

    def test_update_level_not_found(self):
        payload = {"code": "XX", "name": "Inexistant"}

        response = self.client.put(
            "/api/v1/reference/levels/99999/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_delete_level(self):
        level = Level.objects.create(code="6A", name="Sixième année")

        response = self.client.delete(f"/api/v1/reference/levels/{level.id}/")

        assert response.status_code == 204
        assert not Level.objects.filter(pk=level.id).exists()

    def test_delete_level_not_found(self):
        response = self.client.delete("/api/v1/reference/levels/99999/")

        assert response.status_code == 404


@pytest.mark.django_db
class TestParcoursAPI:
    def setup_method(self):
        self.client = Client()
        self.department = Department.objects.create(
            code="SN", name="Sciences du Numerique"
        )
        self.parcours = Parcours.objects.create(
            department=self.department, code="SESG", label="Systèmes Embarqués"
        )

    def test_list_parcours(self):
        response = self.client.get("/api/v1/reference/parcours/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["code"] == "SESG"

    def test_list_parcours_filter_by_department(self):
        dept2 = Department.objects.create(code="TC", name="Tronc Commun")
        Parcours.objects.create(
            department=dept2, code="IPA", label="Ingénierie des Procédés"
        )

        response = self.client.get(
            f"/api/v1/reference/parcours/?department_id={self.department.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["code"] == "SESG"

    def test_select_options(self):
        response = self.client.get("/api/v1/reference/parcours/select-options/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "label" in data[0]

    def test_select_options_filter_by_department(self):
        dept2 = Department.objects.create(code="TC", name="Tronc Commun")
        Parcours.objects.create(
            department=dept2, code="IPA", label="Ingénierie des Procédés"
        )

        response = self.client.get(
            f"/api/v1/reference/parcours/select-options/?department_id={dept2.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["label"].startswith("IPA")

    def test_create_parcours(self):
        payload = {
            "department_id": self.department.id,
            "code": "IPA",
            "label": "Ingénierie des Procédés",
        }

        response = self.client.post(
            "/api/v1/reference/parcours/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json()["code"] == "IPA"
        assert Parcours.objects.filter(code="IPA").exists()

    def test_update_parcours(self):
        payload = {
            "department_id": self.department.id,
            "code": "SESG",
            "label": "Systèmes Embarqués (modifié)",
        }

        response = self.client.put(
            f"/api/v1/reference/parcours/{self.parcours.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["label"] == "Systèmes Embarqués (modifié)"

    def test_update_parcours_not_found(self):
        payload = {
            "department_id": self.department.id,
            "code": "XX",
            "label": "Inexistant",
        }

        response = self.client.put(
            "/api/v1/reference/parcours/99999/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_delete_parcours(self):
        parcours = Parcours.objects.create(
            department=self.department, code="TMP", label="Temporaire"
        )

        response = self.client.delete(f"/api/v1/reference/parcours/{parcours.id}/")

        assert response.status_code == 204
        assert not Parcours.objects.filter(pk=parcours.id).exists()

    def test_delete_parcours_not_found(self):
        response = self.client.delete("/api/v1/reference/parcours/99999/")

        assert response.status_code == 404
