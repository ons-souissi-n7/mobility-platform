import json
from datetime import date

import pytest
from django.test import Client

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import (
    Agreement,
    AgreementQuota,
    RawImport,
    RawImportEntity,
    RawImportStatus,
)
from app.reference.models import Country, CTIRegion, Department


@pytest.mark.django_db
class TestMobilityAgreementAPI:
    def setup_method(self):
        self.client = Client()
        self.country = Country.objects.create(
            iso2="ES",
            name_fr="Espagne",
            name_en="Spain",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )
        self.university = PartnerUniversity.objects.create(
            moveon_id=1001,
            name="Universidad Test",
            country=self.country,
        )
        self.academic_year = AcademicYear.objects.create(
            label="2026-2027",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 8, 31),
        )
        self.department = Department.objects.create(
            code="SN",
            name="Sciences du Numerique",
        )
        self.agreement = Agreement.objects.create(
            moveon_relation_id="REL-001",
            name="Erasmus outgoing agreement",
            partner_university=self.university,
            direction="outgoing",
            status="active",
        )
        self.quota = AgreementQuota.objects.create(
            agreement=self.agreement,
            academic_year=self.academic_year,
            academic_year_label="2026-2027",
            period="S1",
            places_id="PLC-001",
            total_places=4,
            remaining_places=2,
        )

    def test_list_agreements(self):
        response = self.client.get("/api/v1/mobility/agreements/")

        assert response.status_code == 200
        assert response.json()[0]["moveon_relation_id"] == "REL-001"

    def test_create_agreement(self):
        payload = {
            "moveon_relation_id": "REL-002",
            "reference": "REF-002",
            "name": "New Erasmus agreement",
            "partner_university_id": self.university.id,
            "relation_type": "Erasmus",
            "framework": "Erasmus Enseignement",
            "direction": "outgoing",
            "status": "active",
            "is_active": True,
            "start_date": "2026-09-01",
            "end_date": "2027-08-31",
            "start_academic_year": "2026-2027",
            "end_academic_year": "2027-2028",
            "discipline": "Engineering",
            "isced": "071",
            "level": "Master",
            "formation": "SN",
            "url": "",
            "restrictions": "",
            "remarks": "",
            "last_sync_moveon": None,
        }

        response = self.client.post(
            "/api/v1/mobility/agreements/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json()["name"] == "New Erasmus agreement"

    def test_update_agreement(self):
        payload = {
            "moveon_relation_id": "REL-001",
            "reference": "",
            "name": "Updated Erasmus agreement",
            "partner_university_id": self.university.id,
            "relation_type": "",
            "framework": "",
            "direction": "both",
            "status": "active",
            "is_active": True,
            "start_date": None,
            "end_date": None,
            "start_academic_year": "",
            "end_academic_year": "",
            "discipline": "",
            "isced": "",
            "level": "",
            "formation": "",
            "url": "",
            "restrictions": "",
            "remarks": "",
            "last_sync_moveon": None,
        }

        response = self.client.put(
            f"/api/v1/mobility/agreements/{self.agreement.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Erasmus agreement"

    def test_delete_agreement(self):
        agreement = Agreement.objects.create(
            moveon_relation_id="REL-DELETE",
            name="Agreement to delete",
            partner_university=self.university,
        )

        response = self.client.delete(f"/api/v1/mobility/agreements/{agreement.id}/")

        assert response.status_code == 204
        assert not Agreement.objects.filter(pk=agreement.id).exists()

    def test_create_agreement_quota(self):
        payload = {
            "agreement_id": self.agreement.id,
            "academic_year_id": self.academic_year.id,
            "academic_year_label": "2027-2028",
            "period": "S2",
            "places_id": "PLC-002",
            "total_places": 3,
            "remaining_places": 1,
            "total_duration": 12,
            "duration_unit": "months",
            "is_effective": True,
            "remarks": "",
        }

        response = self.client.post(
            "/api/v1/mobility/agreement-quotas/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json()["allocated_places"] == 2

    def test_create_agreement_quota_invalid_remaining_places(self):
        payload = {
            "agreement_id": self.agreement.id,
            "academic_year_id": self.academic_year.id,
            "academic_year_label": "2027-2028",
            "period": "S2",
            "places_id": "PLC-002",
            "total_places": 1,
            "remaining_places": 2,
            "total_duration": None,
            "duration_unit": "",
            "is_effective": True,
            "remarks": "",
        }

        response = self.client.post(
            "/api/v1/mobility/agreement-quotas/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_create_department_quota(self):
        payload = {
            "agreement_quota_id": self.quota.id,
            "department_id": self.department.id,
            "places": 2,
            "remarks": "",
        }

        response = self.client.post(
            "/api/v1/mobility/department-quotas/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        assert response.json()["places"] == 2

    def test_list_raw_imports(self):
        RawImport.objects.create(
            source="moveon_fake",
            source_file="FlowsByInstitutions.xlsx",
            external_id="PLC-001",
            payload={"Places: ID": "PLC-001"},
            status="imported",
        )

        response = self.client.get("/api/v1/mobility/raw-imports/")

        assert response.status_code == 200
        assert response.json()[0]["external_id"] == "PLC-001"

    def test_list_moveon_import_errors(self):
        RawImport.objects.create(
            source="moveon_fake_institutions",
            external_id="3001",
            payload={"country": {"name": "Itallie"}},
            status=RawImportStatus.FAILED,
            error_message="Unknown country name: Itallie",
        )
        RawImport.objects.create(
            source="moveon_fake_agreement",
            entity=RawImportEntity.AGREEMENT,
            external_id="REL-ERR",
            payload={"moveon_relation_id": "REL-ERR", "name": "Broken agreement"},
            status=RawImportStatus.FAILED,
            error_message="partner_university_moveon_id is required",
        )
        response = self.client.get("/api/v1/mobility/raw-imports/moveon-errors/")

        assert response.status_code == 200
        data = response.json()
        assert {item["external_id"] for item in data} == {"REL-ERR"}
        assert "3001" not in {item["external_id"] for item in data}

    def test_retry_agreement_import_with_partner_university_correction(self):
        raw_import = RawImport.objects.create(
            source="moveon_fake_agreement",
            entity=RawImportEntity.AGREEMENT,
            external_id="REL-RETRY",
            payload={"moveon_relation_id": "REL-RETRY", "name": "Retry agreement"},
            status=RawImportStatus.FAILED,
            error_message="partner_university_moveon_id is required",
        )

        response = self.client.put(
            f"/api/v1/mobility/raw-imports/{raw_import.id}/retry/",
            data=json.dumps({"partner_university_id": self.university.id}),
            content_type="application/json",
        )

        assert response.status_code == 200
        raw_import.refresh_from_db()
        assert raw_import.status == RawImportStatus.IMPORTED
        assert Agreement.objects.filter(moveon_relation_id="REL-RETRY").exists()

    def test_ignore_raw_import(self):
        raw_import = RawImport.objects.create(
            source="moveon_fake_institutions",
            external_id="3001",
            payload={"country": {"name": "Itallie"}},
            status=RawImportStatus.FAILED,
            error_message="Unknown country name: Itallie",
        )

        response = self.client.put(
            f"/api/v1/mobility/raw-imports/{raw_import.id}/ignore/"
        )

        assert response.status_code == 200
        raw_import.refresh_from_db()
        assert raw_import.status == RawImportStatus.IGNORED
        assert "Traite manuellement" in raw_import.error_message
