import json
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from app.academic.models import AcademicYear


@pytest.mark.django_db
class TestAcademicYearAPI:
    def setup_method(self):
        self.client = Client()
        self.today = timezone.now().date()
        self.academic_year = AcademicYear.objects.create(
            label="2026-2027",
            start_date=self.today - timedelta(days=30),
            end_date=self.today + timedelta(days=335),
        )

    def test_list_academic_years(self):
        response = self.client.get("/api/v1/academic/years/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["label"] == "2026-2027"

    def test_get_current_academic_year(self):
        response = self.client.get("/api/v1/academic/years/current/")

        assert response.status_code == 200
        assert response.json()["id"] == self.academic_year.id

    def test_create_academic_year(self):
        payload = {
            "label": "2027-2028",
            "start_date": "2027-09-01",
            "end_date": "2028-08-31",
            "wishes_open_date": "2027-10-01",
            "wishes_close_date": "2027-11-01",
            "gpa_freeze_date": "2028-01-15",
            "results_publication_date": "2028-03-15",
        }

        response = self.client.post(
            "/api/v1/academic/years/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "2027-2028"
        assert data["status"] == AcademicYear.CampaignStatus.INITIALIZATION

    def test_update_academic_year(self):
        payload = {
            "label": "2026-2027",
            "start_date": "2026-09-01",
            "end_date": "2027-08-31",
            "wishes_open_date": "2026-10-01",
            "wishes_close_date": "2026-11-01",
            "gpa_freeze_date": None,
            "results_publication_date": None,
        }

        response = self.client.put(
            f"/api/v1/academic/years/{self.academic_year.id}/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["wishes_open_date"] == "2026-10-01"

    def test_delete_academic_year(self):
        response = self.client.delete(
            f"/api/v1/academic/years/{self.academic_year.id}/"
        )

        assert response.status_code == 204
        assert not AcademicYear.objects.filter(pk=self.academic_year.id).exists()

    def test_transition_to_recommendation(self):
        response = self.client.post(
            f"/api/v1/academic/years/{self.academic_year.id}/open-recommendation/"
        )

        assert response.status_code == 200
        assert response.json()["status"] == AcademicYear.CampaignStatus.RECOMMENDATION

    def test_transition_order_returns_400(self):
        response = self.client.post(
            f"/api/v1/academic/years/{self.academic_year.id}/close/"
        )

        assert response.status_code == 400
