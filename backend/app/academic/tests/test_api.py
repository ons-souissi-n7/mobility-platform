import json
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from app.academic.models import AcademicYear
from app.institutions.models import PartnerUniversity
from app.mobility.models import (
    Agreement,
    AgreementDepartment,
    AgreementYear,
    AgreementYearDepartment,
)
from app.reference.models import Country, CTIRegion, Department, Level
from app.students.models import AnnualEnrollment, Student


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

    def test_open_recommendation_requires_dates(self):
        # No wishes_open_date / wishes_close_date → 400
        response = self.client.post(
            f"/api/v1/academic/years/{self.academic_year.id}/open-recommendation/"
        )

        assert response.status_code == 400
        assert "dates" in response.json()["detail"].lower()

    def test_transition_order_returns_400(self):
        # start-candidature requires recommendation state; from initialization → 400
        response = self.client.post(
            f"/api/v1/academic/years/{self.academic_year.id}/start-candidature/"
        )

        assert response.status_code == 400

    def test_launch_assignment_advances_year_and_returns_202(self):
        from unittest.mock import patch

        AcademicYear.objects.filter(pk=self.academic_year.pk).update(status="import")
        with patch("app.academic.api.enqueue_gale_shapley"):
            response = self.client.post(
                f"/api/v1/academic/years/{self.academic_year.id}/launch-assignment/"
            )
        assert response.status_code == 202
        self.academic_year = AcademicYear.objects.get(pk=self.academic_year.pk)
        assert self.academic_year.status == "pre_assignment"

    def test_launch_assignment_returns_409_from_wrong_state(self):
        from unittest.mock import patch

        # Année en 'initialization' — transition interdite
        with patch("app.academic.api.enqueue_gale_shapley"):
            response = self.client.post(
                f"/api/v1/academic/years/{self.academic_year.id}/launch-assignment/"
            )
        assert response.status_code == 409


@pytest.mark.django_db
class TestOpenRecommendationPreconditions:
    """Tests des préconditions métier pour open_recommendation."""

    def setup_method(self):
        self.client = Client()
        self.today = timezone.now().date()
        self.academic_year = AcademicYear.objects.create(
            label="2025-2026",
            start_date=self.today - timedelta(days=30),
            end_date=self.today + timedelta(days=335),
            wishes_open_date=self.today + timedelta(days=1),
            wishes_close_date=self.today + timedelta(days=30),
        )

    def _create_enrollment_with_gpa(self):
        dept = Department.objects.create(code="GE", name="Génie Electrique")
        level = Level.objects.create(code="3A", name="Troisième année")
        student = Student.objects.create(
            ine="12345678901", first_name="Alice", last_name="Martin"
        )
        return AnnualEnrollment.objects.create(
            student=student,
            academic_year=self.academic_year,
            department=dept,
            level=level,
            gpa="14.50",
        )

    def _create_agreement_with_quota(self):
        country = Country.objects.create(
            iso2="DE",
            name_fr="Allemagne",
            name_en="Germany",
            cti_region=CTIRegion.EUROPE_HORS_FRANCE,
        )
        univ = PartnerUniversity.objects.create(name="TU Berlin", country=country)
        agreement = Agreement.objects.create(
            name="Erasmus TU Berlin",
            partner_university=univ,
            inp_total_places=4,
        )
        dept = Department.objects.get_or_create(
            code="GE", defaults={"name": "Génie Electrique"}
        )[0]
        ag_year = AgreementYear.objects.create(
            agreement=agreement,
            academic_year=self.academic_year,
            is_active=True,
        )
        ag_dept = AgreementDepartment.objects.create(
            agreement=agreement, department=dept
        )
        AgreementYearDepartment.objects.create(
            agreement_year=ag_year,
            agreement_department=ag_dept,
            estimated_places=2,
        )
        return ag_year

    def test_requires_gpa(self):
        # Dates set but no enrolled student with GPA → 400
        response = self.client.post(
            f"/api/v1/academic/years/{self.academic_year.id}/open-recommendation/"
        )
        assert response.status_code == 400
        assert "GPA" in response.json()["detail"]

    def test_requires_quotas(self):
        # Dates + GPA present but no department quota → 400
        self._create_enrollment_with_gpa()
        response = self.client.post(
            f"/api/v1/academic/years/{self.academic_year.id}/open-recommendation/"
        )
        assert response.status_code == 400
        assert "quota" in response.json()["detail"].lower()

    def test_success(self):
        # All preconditions met → 200 + status = recommendation
        self._create_enrollment_with_gpa()
        self._create_agreement_with_quota()
        response = self.client.post(
            f"/api/v1/academic/years/{self.academic_year.id}/open-recommendation/"
        )
        assert response.status_code == 200
        assert response.json()["status"] == AcademicYear.CampaignStatus.RECOMMENDATION
